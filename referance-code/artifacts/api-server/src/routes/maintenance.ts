import { Router } from "express";
import { eq } from "drizzle-orm";
import { db, maintenanceTicketsTable, unitsTable, propertiesTable, usersTable } from "@workspace/db";
import { requireAuth } from "../middlewares/auth";

const router = Router();

async function formatTicket(ticket: typeof maintenanceTicketsTable.$inferSelect) {
  const [unit] = await db.select().from(unitsTable).where(eq(unitsTable.id, ticket.unitId));
  let propertyName: string | null = null;
  if (unit) {
    const [prop] = await db.select().from(propertiesTable).where(eq(propertiesTable.id, unit.propertyId));
    propertyName = prop?.name ?? null;
  }
  const [reporter] = await db.select().from(usersTable).where(eq(usersTable.id, ticket.reportedById));
  let assignedToName: string | null = null;
  if (ticket.assignedToId) {
    const [assignee] = await db.select().from(usersTable).where(eq(usersTable.id, ticket.assignedToId));
    assignedToName = assignee?.fullName ?? null;
  }
  return {
    id: ticket.id,
    unitId: ticket.unitId,
    unitNumber: unit?.unitNumber ?? null,
    propertyName,
    reportedById: ticket.reportedById,
    reportedByName: reporter?.fullName ?? null,
    assignedToId: ticket.assignedToId ?? null,
    assignedToName,
    title: ticket.title,
    description: ticket.description,
    urgency: ticket.urgency,
    status: ticket.status,
    cost: ticket.cost ? parseFloat(ticket.cost) : null,
    createdAt: ticket.createdAt.toISOString(),
    resolvedAt: ticket.resolvedAt?.toISOString() ?? null,
  };
}

router.get("/maintenance", requireAuth, async (req, res): Promise<void> => {
  const { status, urgency } = req.query;
  let tickets = await db.select().from(maintenanceTicketsTable).orderBy(maintenanceTicketsTable.createdAt);
  if (status) tickets = tickets.filter((t) => t.status === status);
  if (urgency) tickets = tickets.filter((t) => t.urgency === urgency);
  res.json(await Promise.all(tickets.map(formatTicket)));
});

router.post("/maintenance", requireAuth, async (req, res): Promise<void> => {
  const { unitId, title, description, urgency } = req.body;
  if (!unitId || !title || !description || !urgency) {
    res.status(400).json({ error: "Missing required fields" });
    return;
  }
  if (!req.session.userId) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }
  const [ticket] = await db.insert(maintenanceTicketsTable).values({
    unitId,
    reportedById: req.session.userId,
    title,
    description,
    urgency,
  }).returning();
  res.status(201).json(await formatTicket(ticket));
});

router.get("/maintenance/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [ticket] = await db.select().from(maintenanceTicketsTable).where(eq(maintenanceTicketsTable.id, id));
  if (!ticket) {
    res.status(404).json({ error: "Ticket not found" });
    return;
  }
  res.json(await formatTicket(ticket));
});

router.put("/maintenance/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const { status, assignedToId, cost, urgency } = req.body;
  const resolvedAt = status === "RESOLVED" ? new Date() : undefined;
  const [ticket] = await db.update(maintenanceTicketsTable).set({
    ...(status && { status }),
    ...(assignedToId != null && { assignedToId }),
    ...(cost != null && { cost: String(cost) }),
    ...(urgency && { urgency }),
    ...(resolvedAt && { resolvedAt }),
  }).where(eq(maintenanceTicketsTable.id, id)).returning();
  if (!ticket) {
    res.status(404).json({ error: "Ticket not found" });
    return;
  }
  res.json(await formatTicket(ticket));
});

export default router;
