import { Router } from "express";
import { eq, and } from "drizzle-orm";
import { db, unitsTable, propertiesTable, tenantsTable, leasesTable } from "@workspace/db";
import { requireAuth } from "../middlewares/auth";

const router = Router();

async function formatUnit(unit: typeof unitsTable.$inferSelect) {
  const [prop] = await db.select().from(propertiesTable).where(eq(propertiesTable.id, unit.propertyId));
  let currentTenantName: string | null = null;
  if (unit.status === "OCCUPIED") {
    const [lease] = await db.select().from(leasesTable)
      .where(and(eq(leasesTable.unitId, unit.id), eq(leasesTable.isActive, true)));
    if (lease) {
      const [tenant] = await db.select().from(tenantsTable).where(eq(tenantsTable.id, lease.tenantId));
      currentTenantName = tenant?.fullName ?? null;
    }
  }
  return {
    id: unit.id,
    propertyId: unit.propertyId,
    propertyName: prop?.name ?? null,
    unitNumber: unit.unitNumber,
    unitType: unit.unitType,
    bedrooms: unit.bedrooms,
    monthlyRent: parseFloat(unit.monthlyRent),
    status: unit.status,
    currentTenantName,
  };
}

router.get("/properties/:propertyId/units", requireAuth, async (req, res): Promise<void> => {
  const propertyId = parseInt(Array.isArray(req.params.propertyId) ? req.params.propertyId[0] : req.params.propertyId, 10);
  const { status } = req.query;
  let units = await db.select().from(unitsTable).where(eq(unitsTable.propertyId, propertyId));
  if (status) units = units.filter((u) => u.status === status);
  res.json(await Promise.all(units.map(formatUnit)));
});

router.post("/properties/:propertyId/units", requireAuth, async (req, res): Promise<void> => {
  const propertyId = parseInt(Array.isArray(req.params.propertyId) ? req.params.propertyId[0] : req.params.propertyId, 10);
  const { unitNumber, unitType, bedrooms, monthlyRent, status } = req.body;
  if (!unitNumber || !unitType || monthlyRent == null) {
    res.status(400).json({ error: "Missing required fields" });
    return;
  }
  const [unit] = await db.insert(unitsTable).values({
    propertyId,
    unitNumber,
    unitType: unitType ?? "APARTMENT",
    bedrooms: bedrooms ?? 0,
    monthlyRent: String(monthlyRent),
    status: status ?? "VACANT",
  }).returning();
  res.status(201).json(await formatUnit(unit));
});

router.get("/units", requireAuth, async (req, res): Promise<void> => {
  const { status } = req.query;
  let units = await db.select().from(unitsTable);
  if (status) units = units.filter((u) => u.status === status);
  res.json(await Promise.all(units.map(formatUnit)));
});

router.get("/units/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [unit] = await db.select().from(unitsTable).where(eq(unitsTable.id, id));
  if (!unit) {
    res.status(404).json({ error: "Unit not found" });
    return;
  }
  res.json(await formatUnit(unit));
});

router.put("/units/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const { unitNumber, unitType, bedrooms, monthlyRent, status } = req.body;
  const [unit] = await db.update(unitsTable).set({
    ...(unitNumber && { unitNumber }),
    ...(unitType && { unitType }),
    ...(bedrooms != null && { bedrooms }),
    ...(monthlyRent != null && { monthlyRent: String(monthlyRent) }),
    ...(status && { status }),
  }).where(eq(unitsTable.id, id)).returning();
  if (!unit) {
    res.status(404).json({ error: "Unit not found" });
    return;
  }
  res.json(await formatUnit(unit));
});

router.delete("/units/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [unit] = await db.delete(unitsTable).where(eq(unitsTable.id, id)).returning();
  if (!unit) {
    res.status(404).json({ error: "Unit not found" });
    return;
  }
  res.json({ message: "Unit deleted" });
});

export default router;
