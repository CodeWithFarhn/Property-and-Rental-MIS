import { Router } from "express";
import { eq, and } from "drizzle-orm";
import { db, leasesTable, tenantsTable, unitsTable, propertiesTable } from "@workspace/db";
import { requireAuth } from "../middlewares/auth";

const router = Router();

async function formatLease(lease: typeof leasesTable.$inferSelect) {
  const [tenant] = await db.select().from(tenantsTable).where(eq(tenantsTable.id, lease.tenantId));
  const [unit] = await db.select().from(unitsTable).where(eq(unitsTable.id, lease.unitId));
  let propertyName: string | null = null;
  if (unit) {
    const [prop] = await db.select().from(propertiesTable).where(eq(propertiesTable.id, unit.propertyId));
    propertyName = prop?.name ?? null;
  }
  return {
    id: lease.id,
    tenantId: lease.tenantId,
    tenantName: tenant?.fullName ?? null,
    unitId: lease.unitId,
    unitNumber: unit?.unitNumber ?? null,
    propertyName,
    startDate: lease.startDate,
    endDate: lease.endDate ?? null,
    monthlyRent: parseFloat(lease.monthlyRent),
    depositAmount: parseFloat(lease.depositAmount),
    depositPaid: lease.depositPaid,
    isActive: lease.isActive,
    notes: lease.notes ?? null,
  };
}

router.get("/leases", requireAuth, async (req, res): Promise<void> => {
  const { isActive, tenantId } = req.query;
  let leases = await db.select().from(leasesTable).orderBy(leasesTable.createdAt);
  if (isActive !== undefined) {
    const active = isActive === "true";
    leases = leases.filter((l) => l.isActive === active);
  }
  if (tenantId) {
    const tid = parseInt(tenantId as string, 10);
    leases = leases.filter((l) => l.tenantId === tid);
  }
  res.json(await Promise.all(leases.map(formatLease)));
});

router.post("/leases", requireAuth, async (req, res): Promise<void> => {
  const { tenantId, unitId, startDate, endDate, monthlyRent, depositAmount, depositPaid, notes } = req.body;
  if (!tenantId || !unitId || !startDate || monthlyRent == null) {
    res.status(400).json({ error: "Missing required fields" });
    return;
  }

  const existingLeases = await db.select().from(leasesTable)
    .where(and(eq(leasesTable.unitId, unitId), eq(leasesTable.isActive, true)));
  if (existingLeases.length > 0) {
    res.status(400).json({ error: "Unit already has an active lease" });
    return;
  }

  const [lease] = await db.insert(leasesTable).values({
    tenantId,
    unitId,
    startDate,
    endDate: endDate ?? null,
    monthlyRent: String(monthlyRent),
    depositAmount: String(depositAmount ?? 0),
    depositPaid: depositPaid ?? false,
    notes: notes ?? null,
  }).returning();

  await db.update(unitsTable).set({ status: "OCCUPIED" }).where(eq(unitsTable.id, unitId));

  res.status(201).json(await formatLease(lease));
});

router.get("/leases/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [lease] = await db.select().from(leasesTable).where(eq(leasesTable.id, id));
  if (!lease) {
    res.status(404).json({ error: "Lease not found" });
    return;
  }
  res.json(await formatLease(lease));
});

router.put("/leases/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const { endDate, monthlyRent, depositPaid, notes } = req.body;
  const [lease] = await db.update(leasesTable).set({
    ...(endDate != null && { endDate }),
    ...(monthlyRent != null && { monthlyRent: String(monthlyRent) }),
    ...(depositPaid != null && { depositPaid }),
    ...(notes != null && { notes }),
  }).where(eq(leasesTable.id, id)).returning();
  if (!lease) {
    res.status(404).json({ error: "Lease not found" });
    return;
  }
  res.json(await formatLease(lease));
});

router.post("/leases/:id/terminate", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [lease] = await db.update(leasesTable).set({ isActive: false }).where(eq(leasesTable.id, id)).returning();
  if (!lease) {
    res.status(404).json({ error: "Lease not found" });
    return;
  }
  await db.update(unitsTable).set({ status: "VACANT" }).where(eq(unitsTable.id, lease.unitId));
  res.json(await formatLease(lease));
});

export default router;
