import { Router } from "express";
import { eq, and, lt, gte, sql } from "drizzle-orm";
import {
  db,
  propertiesTable,
  unitsTable,
  tenantsTable,
  leasesTable,
  invoicesTable,
  paymentsTable,
  maintenanceTicketsTable,
} from "@workspace/db";
import { requireAuth } from "../middlewares/auth";

const router = Router();

router.get("/dashboard/summary", requireAuth, async (req, res): Promise<void> => {
  const properties = await db.select().from(propertiesTable);
  const units = await db.select().from(unitsTable);
  const tenants = await db.select().from(tenantsTable).where(eq(tenantsTable.status, "ACTIVE"));
  const activeLeases = await db.select().from(leasesTable).where(eq(leasesTable.isActive, true));
  const allInvoices = await db.select().from(invoicesTable);
  const openTickets = await db.select().from(maintenanceTicketsTable);

  const vacantUnits = units.filter((u) => u.status === "VACANT").length;
  const occupiedUnits = units.filter((u) => u.status === "OCCUPIED").length;
  const totalUnits = units.length;
  const occupancyRate = totalUnits > 0 ? Math.round((occupiedUnits / totalUnits) * 100) : 0;

  const monthlyRevenuePotential = activeLeases.reduce((sum, l) => sum + parseFloat(l.monthlyRent), 0);

  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split("T")[0];
  const thisMonthPayments = await db.select().from(paymentsTable).where(gte(paymentsTable.datePaid, startOfMonth));
  const collectedThisMonth = thisMonthPayments.reduce((sum, p) => sum + parseFloat(p.amountPaid), 0);

  const today = now.toISOString().split("T")[0];
  const overdueInvoices = allInvoices.filter((i) => i.status !== "PAID" && i.dueDate < today);
  const overdueAmount = overdueInvoices.reduce((sum, i) => sum + (parseFloat(i.amountDue) - parseFloat(i.amountPaid)), 0);

  const openMaintenanceTickets = openTickets.filter((t) => t.status === "OPEN" || t.status === "IN_PROGRESS").length;
  const criticalTickets = openTickets.filter((t) => t.urgency === "CRITICAL" && t.status !== "RESOLVED" && t.status !== "CLOSED").length;

  res.json({
    totalProperties: properties.length,
    totalUnits,
    vacantUnits,
    occupiedUnits,
    occupancyRate,
    totalTenants: tenants.length,
    activeLeases: activeLeases.length,
    monthlyRevenuePotential,
    collectedThisMonth,
    overdueAmount,
    openMaintenanceTickets,
    criticalTickets,
  });
});

router.get("/dashboard/occupancy", requireAuth, async (req, res): Promise<void> => {
  const properties = await db.select().from(propertiesTable);
  const result = await Promise.all(
    properties.map(async (prop) => {
      const units = await db.select().from(unitsTable).where(eq(unitsTable.propertyId, prop.id));
      const total = units.length;
      const vacant = units.filter((u) => u.status === "VACANT").length;
      const occupied = units.filter((u) => u.status === "OCCUPIED").length;
      const maintenance = units.filter((u) => u.status === "MAINTENANCE").length;
      return {
        propertyId: prop.id,
        propertyName: prop.name,
        totalUnits: total,
        vacantUnits: vacant,
        occupiedUnits: occupied,
        maintenanceUnits: maintenance,
        occupancyRate: total > 0 ? Math.round((occupied / total) * 100) : 0,
      };
    })
  );
  res.json(result);
});

router.get("/dashboard/revenue", requireAuth, async (req, res): Promise<void> => {
  const result: { month: string; invoiced: number; collected: number }[] = [];
  const now = new Date();
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const monthStart = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
    const nextMonth = new Date(d.getFullYear(), d.getMonth() + 1, 1);
    const monthEnd = `${nextMonth.getFullYear()}-${String(nextMonth.getMonth() + 1).padStart(2, "0")}-01`;
    const monthLabel = d.toLocaleString("default", { month: "short", year: "numeric" });

    const invoices = await db.select().from(invoicesTable)
      .where(and(gte(invoicesTable.periodMonth, monthStart), lt(invoicesTable.periodMonth, monthEnd)));
    const payments = await db.select().from(paymentsTable)
      .where(and(gte(paymentsTable.datePaid, monthStart), lt(paymentsTable.datePaid, monthEnd)));

    result.push({
      month: monthLabel,
      invoiced: invoices.reduce((s, i) => s + parseFloat(i.amountDue), 0),
      collected: payments.reduce((s, p) => s + parseFloat(p.amountPaid), 0),
    });
  }
  res.json(result);
});

router.get("/dashboard/overdue", requireAuth, async (req, res): Promise<void> => {
  const today = new Date().toISOString().split("T")[0];
  const allInvoices = await db.select().from(invoicesTable);
  const overdueInvoices = allInvoices.filter((i) => i.status !== "PAID" && i.dueDate < today);

  const result = await Promise.all(
    overdueInvoices.map(async (inv) => {
      const [lease] = await db.select().from(leasesTable).where(eq(leasesTable.id, inv.leaseId));
      if (!lease) return null;
      const [tenant] = await db.select().from(tenantsTable).where(eq(tenantsTable.id, lease.tenantId));
      const [unit] = await db.select().from(unitsTable).where(eq(unitsTable.id, lease.unitId));
      let propertyName = "";
      if (unit) {
        const [prop] = await db.select().from(propertiesTable).where(eq(propertiesTable.id, unit.propertyId));
        propertyName = prop?.name ?? "";
      }
      const dueDate = new Date(inv.dueDate);
      const daysOverdue = Math.floor((Date.now() - dueDate.getTime()) / (1000 * 60 * 60 * 24));
      return {
        id: inv.id,
        invoiceNumber: inv.invoiceNumber,
        tenantName: tenant?.fullName ?? "Unknown",
        tenantPhone: tenant?.phone ?? "",
        unitNumber: unit?.unitNumber ?? "",
        propertyName,
        amountDue: parseFloat(inv.amountDue),
        amountPaid: parseFloat(inv.amountPaid),
        dueDate: inv.dueDate,
        daysOverdue,
      };
    })
  );
  res.json(result.filter(Boolean));
});

router.get("/dashboard/recent-activity", requireAuth, async (req, res): Promise<void> => {
  const activity: { id: string; type: string; description: string; timestamp: string; relatedId: number | null }[] = [];

  const recentPayments = await db.select().from(paymentsTable).orderBy(paymentsTable.createdAt);
  const recentLeases = await db.select().from(leasesTable).orderBy(leasesTable.createdAt);
  const recentTickets = await db.select().from(maintenanceTicketsTable).orderBy(maintenanceTicketsTable.createdAt);
  const recentTenants = await db.select().from(tenantsTable).orderBy(tenantsTable.createdAt);

  for (const p of recentPayments.slice(-5)) {
    activity.push({
      id: `payment-${p.id}`,
      type: "PAYMENT",
      description: `Payment of PKR ${parseFloat(p.amountPaid).toLocaleString()} recorded`,
      timestamp: p.createdAt.toISOString(),
      relatedId: p.id,
    });
  }
  for (const l of recentLeases.slice(-5)) {
    activity.push({
      id: `lease-${l.id}`,
      type: "LEASE",
      description: l.isActive ? `New lease created` : `Lease terminated`,
      timestamp: l.createdAt.toISOString(),
      relatedId: l.id,
    });
  }
  for (const t of recentTickets.slice(-5)) {
    activity.push({
      id: `maintenance-${t.id}`,
      type: "MAINTENANCE",
      description: `Maintenance ticket: ${t.title}`,
      timestamp: t.createdAt.toISOString(),
      relatedId: t.id,
    });
  }
  for (const t of recentTenants.slice(-3)) {
    activity.push({
      id: `tenant-${t.id}`,
      type: "TENANT",
      description: `New tenant onboarded: ${t.fullName}`,
      timestamp: t.createdAt.toISOString(),
      relatedId: t.id,
    });
  }

  activity.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  res.json(activity.slice(0, 15));
});

export default router;
