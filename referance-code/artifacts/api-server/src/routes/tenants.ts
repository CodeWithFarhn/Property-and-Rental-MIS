import { Router } from "express";
import { eq } from "drizzle-orm";
import { db, tenantsTable, leasesTable, unitsTable, propertiesTable } from "@workspace/db";
import { requireAuth } from "../middlewares/auth";

const router = Router();

async function formatTenant(tenant: typeof tenantsTable.$inferSelect) {
  const [activeLease] = await db.select().from(leasesTable)
    .where(eq(leasesTable.tenantId, tenant.id));
  const activeLeases = await db.select().from(leasesTable)
    .where(eq(leasesTable.tenantId, tenant.id));
  const activeLease2 = activeLeases.find((l) => l.isActive);

  let unitNumber: string | null = null;
  let propertyName: string | null = null;

  if (activeLease2) {
    const [unit] = await db.select().from(unitsTable).where(eq(unitsTable.id, activeLease2.unitId));
    if (unit) {
      unitNumber = unit.unitNumber;
      const [prop] = await db.select().from(propertiesTable).where(eq(propertiesTable.id, unit.propertyId));
      propertyName = prop?.name ?? null;
    }
  }

  return {
    id: tenant.id,
    fullName: tenant.fullName,
    email: tenant.email,
    phone: tenant.phone,
    cnic: tenant.cnic,
    profession: tenant.profession ?? null,
    emergencyContact: tenant.emergencyContact ?? null,
    accountBalance: parseFloat(tenant.accountBalance),
    status: tenant.status,
    createdAt: tenant.createdAt.toISOString(),
    activeLeaseId: activeLease2?.id ?? null,
    unitNumber,
    propertyName,
  };
}

router.get("/tenants", requireAuth, async (req, res): Promise<void> => {
  const { status } = req.query;
  let tenants = await db.select().from(tenantsTable).orderBy(tenantsTable.createdAt);
  if (status) tenants = tenants.filter((t) => t.status === status);
  res.json(await Promise.all(tenants.map(formatTenant)));
});

router.post("/tenants", requireAuth, async (req, res): Promise<void> => {
  const { fullName, email, phone, cnic, profession, emergencyContact } = req.body;
  if (!fullName || !email || !phone || !cnic) {
    res.status(400).json({ error: "Missing required fields" });
    return;
  }
  const [tenant] = await db.insert(tenantsTable).values({
    fullName, email, phone, cnic,
    profession: profession ?? null,
    emergencyContact: emergencyContact ?? null,
  }).returning();
  res.status(201).json(await formatTenant(tenant));
});

router.get("/tenants/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const [tenant] = await db.select().from(tenantsTable).where(eq(tenantsTable.id, id));
  if (!tenant) {
    res.status(404).json({ error: "Tenant not found" });
    return;
  }
  res.json(await formatTenant(tenant));
});

router.put("/tenants/:id", requireAuth, async (req, res): Promise<void> => {
  const id = parseInt(Array.isArray(req.params.id) ? req.params.id[0] : req.params.id, 10);
  const { fullName, email, phone, profession, emergencyContact, status } = req.body;
  const [tenant] = await db.update(tenantsTable).set({
    ...(fullName && { fullName }),
    ...(email && { email }),
    ...(phone && { phone }),
    ...(profession != null && { profession }),
    ...(emergencyContact != null && { emergencyContact }),
    ...(status && { status }),
  }).where(eq(tenantsTable.id, id)).returning();
  if (!tenant) {
    res.status(404).json({ error: "Tenant not found" });
    return;
  }
  res.json(await formatTenant(tenant));
});

export default router;
