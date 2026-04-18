import { Router } from "express";
import { eq } from "drizzle-orm";
import { db, invoicesTable, paymentsTable, leasesTable, tenantsTable, unitsTable, propertiesTable, usersTable } from "@workspace/db";
import { requireAuth } from "../middlewares/auth";

const router = Router();

async function formatInvoice(inv: typeof invoicesTable.$inferSelect) {
  const [lease] = await db.select().from(leasesTable).where(eq(leasesTable.id, inv.leaseId));
  let tenantName: string | null = null;
  let unitNumber: string | null = null;
  let propertyName: string | null = null;
  if (lease) {
    const [tenant] = await db.select().from(tenantsTable).where(eq(tenantsTable.id, lease.tenantId));
    tenantName = tenant?.fullName ?? null;
    const [unit] = await db.select().from(unitsTable).where(eq(unitsTable.id, lease.unitId));
    if (unit) {
      unitNumber = unit.unitNumber;
      const [prop] = await db.select().from(propertiesTable).where(eq(propertiesTable.id, unit.propertyId));
      propertyName = prop?.name ?? null;
    }
  }
  return {
    id: inv.id,
    invoiceNumber: inv.invoiceNumber,
    leaseId: inv.leaseId,
    tenantName,
    unitNumber,
    propertyName,
    periodMonth: inv.periodMonth,
    amountDue: parseFloat(inv.amountDue),
    amountPaid: parseFloat(inv.amountPaid),
    dueDate: inv.dueDate,
    status: inv.status,
    notes: inv.notes ?? null,
    createdAt: inv.createdAt.toISOString(),
  };
}

async function formatPayment(p: typeof paymentsTable.$inferSelect) {
  const [invoice] = await db.select().from(invoicesTable).where(eq(invoicesTable.id, p.invoiceId));
  const [recorder] = await db.select().from(usersTable).where(eq(usersTable.id, p.recordedById));
  return {
    id: p.id,
    invoiceId: p.invoiceId,
    invoiceNumber: invoice?.invoiceNumber ?? null,
    amountPaid: parseFloat(p.amountPaid),
    paymentMethod: p.paymentMethod,
    referenceCode: p.referenceCode ?? null,
    recordedById: p.recordedById,
    recordedByName: recorder?.fullName ?? null,
    datePaid: p.datePaid,
    notes: p.notes ?? null,
  };
}

router.get("/invoices", requireAuth, async (req, res): Promise<void> => {
  const { status, leaseId } = req.query;
  let invoices = await db.select().from(invoicesTable).orderBy(invoicesTable.createdAt);
  if (status) invoices = invoices.filter((i) => i.status === status);
  if (leaseId) invoices = invoices.filter((i) => i.leaseId === parseInt(leaseId as string, 10));
  res.json(await Promise.all(invoices.map(formatInvoice)));
});

router.post("/invoices", requireAuth, async (req, res): Promise<void> => {
  const { leaseId, periodMonth, amountDue, dueDate, notes } = req.body;
  if (!leaseId || !periodMonth || amountDue == null || !dueDate) {
    res.status(400).json({ error: "Missing required fields" });
    return;
  }
  const invoiceNumber = `INV-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}`;
  const [inv] = await db.insert(invoicesTable).values({
    invoiceNumber,
    leaseId,
    periodMonth,
    amountDue: String(amountDue),
    dueDate,
    notes: notes ?? null,
  }).returning();
  res.status(201).json(await formatInvoice(inv));
});

router.get("/invoices/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [inv] = await db.select().from(invoicesTable).where(eq(invoicesTable.id, id));
  if (!inv) {
    res.status(404).json({ error: "Invoice not found" });
    return;
  }
  res.json(await formatInvoice(inv));
});

router.get("/payments", requireAuth, async (req, res): Promise<void> => {
  const { invoiceId } = req.query;
  let payments = await db.select().from(paymentsTable).orderBy(paymentsTable.createdAt);
  if (invoiceId) payments = payments.filter((p) => p.invoiceId === parseInt(invoiceId as string, 10));
  res.json(await Promise.all(payments.map(formatPayment)));
});

router.post("/payments", requireAuth, async (req, res): Promise<void> => {
  const { invoiceId, amountPaid, paymentMethod, referenceCode, datePaid, notes } = req.body;
  if (!invoiceId || amountPaid == null || !paymentMethod || !datePaid) {
    res.status(400).json({ error: "Missing required fields" });
    return;
  }
  if (!req.session.userId) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }

  const [inv] = await db.select().from(invoicesTable).where(eq(invoicesTable.id, invoiceId));
  if (!inv) {
    res.status(404).json({ error: "Invoice not found" });
    return;
  }

  const [payment] = await db.insert(paymentsTable).values({
    invoiceId,
    amountPaid: String(amountPaid),
    paymentMethod,
    referenceCode: referenceCode ?? null,
    recordedById: req.session.userId,
    datePaid,
    notes: notes ?? null,
  }).returning();

  const newAmountPaid = parseFloat(inv.amountPaid) + parseFloat(String(amountPaid));
  const newStatus = newAmountPaid >= parseFloat(inv.amountDue) ? "PAID"
    : newAmountPaid > 0 ? "PARTIAL"
    : "UNPAID";
  await db.update(invoicesTable).set({
    amountPaid: String(newAmountPaid),
    status: newStatus,
  }).where(eq(invoicesTable.id, invoiceId));

  res.status(201).json(await formatPayment(payment));
});

router.get("/payments/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [p] = await db.select().from(paymentsTable).where(eq(paymentsTable.id, id));
  if (!p) {
    res.status(404).json({ error: "Payment not found" });
    return;
  }
  res.json(await formatPayment(p));
});

export default router;
