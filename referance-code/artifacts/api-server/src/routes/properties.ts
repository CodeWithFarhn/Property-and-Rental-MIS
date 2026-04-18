import { Router } from "express";
import { eq, and, sql } from "drizzle-orm";
import { db, propertiesTable, unitsTable, usersTable } from "@workspace/db";
import { requireAuth } from "../middlewares/auth";

const router = Router();

async function formatProperty(prop: typeof propertiesTable.$inferSelect) {
  const units = await db.select().from(unitsTable).where(eq(unitsTable.propertyId, prop.id));
  const owner = await db.select().from(usersTable).where(eq(usersTable.id, prop.ownerId));
  return {
    id: prop.id,
    name: prop.name,
    address: prop.address,
    location: prop.location,
    ownerId: prop.ownerId,
    ownerName: owner[0]?.fullName ?? null,
    totalUnits: units.length,
    vacantUnits: units.filter((u) => u.status === "VACANT").length,
    occupiedUnits: units.filter((u) => u.status === "OCCUPIED").length,
    maintenanceUnits: units.filter((u) => u.status === "MAINTENANCE").length,
    createdAt: prop.createdAt.toISOString(),
  };
}

router.get("/properties", requireAuth, async (req, res): Promise<void> => {
  const props = await db.select().from(propertiesTable).orderBy(propertiesTable.createdAt);
  const result = await Promise.all(props.map(formatProperty));
  res.json(result);
});

router.post("/properties", requireAuth, async (req, res): Promise<void> => {
  const { name, address, location, ownerId } = req.body;
  if (!name || !address || !location || !ownerId) {
    res.status(400).json({ error: "Missing required fields" });
    return;
  }
  const [prop] = await db.insert(propertiesTable).values({ name, address, location, ownerId }).returning();
  res.status(201).json(await formatProperty(prop));
});

router.get("/properties/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [prop] = await db.select().from(propertiesTable).where(eq(propertiesTable.id, id));
  if (!prop) {
    res.status(404).json({ error: "Property not found" });
    return;
  }
  res.json(await formatProperty(prop));
});

router.put("/properties/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const { name, address, location, ownerId } = req.body;
  const [prop] = await db.update(propertiesTable).set({
    ...(name && { name }),
    ...(address && { address }),
    ...(location && { location }),
    ...(ownerId && { ownerId }),
  }).where(eq(propertiesTable.id, id)).returning();
  if (!prop) {
    res.status(404).json({ error: "Property not found" });
    return;
  }
  res.json(await formatProperty(prop));
});

router.delete("/properties/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [prop] = await db.delete(propertiesTable).where(eq(propertiesTable.id, id)).returning();
  if (!prop) {
    res.status(404).json({ error: "Property not found" });
    return;
  }
  res.json({ message: "Property deleted" });
});

export default router;
