import { useParams, Link } from "wouter";
import { 
  useGetTenant, 
  useListLeases, 
  useListInvoices, 
  useListPayments,
  getGetTenantQueryKey,
  getListLeasesQueryKey,
  getListInvoicesQueryKey,
  getListPaymentsQueryKey
} from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ArrowLeft, User, Phone, Mail, FileText, CreditCard } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

export default function TenantDetail() {
  const { id } = useParams<{ id: string }>();
  const tenantId = Number(id);

  const { data: tenant, isLoading: loadingTenant } = useGetTenant(tenantId, {
    query: { enabled: !!tenantId, queryKey: getGetTenantQueryKey(tenantId) }
  });

  const { data: leases, isLoading: loadingLeases } = useListLeases({ tenantId }, {
    query: { enabled: !!tenantId, queryKey: getListLeasesQueryKey({ tenantId }) }
  });

  const { data: invoices, isLoading: loadingInvoices } = useListInvoices(undefined, {
    query: { queryKey: getListInvoicesQueryKey() }
  });

  const tenantInvoices = invoices?.filter(inv => leases?.some(l => l.id === inv.leaseId)) || [];
  
  if (loadingTenant || loadingLeases || loadingInvoices) return <div>Loading...</div>;
  if (!tenant) return <div>Tenant not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" asChild>
          <Link href="/tenants"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">{tenant.fullName}</h1>
        {tenant.status === "ACTIVE" ? 
          <Badge className="bg-green-500">Active</Badge> : 
          <Badge variant="secondary">Inactive</Badge>
        }
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Contact Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <User className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="text-sm font-medium">CNIC</div>
                <div className="text-sm text-muted-foreground">{tenant.cnic}</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Phone className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="text-sm font-medium">Phone</div>
                <div className="text-sm text-muted-foreground">{tenant.phone}</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="text-sm font-medium">Email</div>
                <div className="text-sm text-muted-foreground">{tenant.email}</div>
              </div>
            </div>
            {tenant.profession && (
              <div className="flex justify-between border-t pt-2 mt-2">
                <span className="text-sm text-muted-foreground">Profession</span>
                <span className="text-sm font-medium">{tenant.profession}</span>
              </div>
            )}
            {tenant.emergencyContact && (
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Emergency</span>
                <span className="text-sm font-medium">{tenant.emergencyContact}</span>
              </div>
            )}
            <div className="flex justify-between border-t pt-2">
              <span className="text-sm font-medium">Balance</span>
              <span className={`text-sm font-bold ${tenant.accountBalance < 0 ? "text-destructive" : "text-green-600"}`}>
                {formatCurrency(tenant.accountBalance)}
              </span>
            </div>
          </CardContent>
        </Card>

        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Leases</CardTitle>
              <Button size="sm" variant="outline" asChild>
                <Link href={`/leases/new?tenantId=${tenant.id}`}>New Lease</Link>
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Property / Unit</TableHead>
                    <TableHead>Dates</TableHead>
                    <TableHead>Rent</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leases?.map(lease => (
                    <TableRow key={lease.id}>
                      <TableCell>
                        <div className="font-medium">{lease.unitNumber}</div>
                        <div className="text-xs text-muted-foreground">{lease.propertyName}</div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">{new Date(lease.startDate).toLocaleDateString()}</div>
                        <div className="text-xs text-muted-foreground">to {lease.endDate ? new Date(lease.endDate).toLocaleDateString() : 'Ongoing'}</div>
                      </TableCell>
                      <TableCell>{formatCurrency(lease.monthlyRent)}</TableCell>
                      <TableCell>
                        {lease.isActive ? <Badge>Active</Badge> : <Badge variant="secondary">Terminated</Badge>}
                      </TableCell>
                    </TableRow>
                  ))}
                  {leases?.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-4 text-muted-foreground">No leases found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Invoices</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Invoice #</TableHead>
                    <TableHead>Period</TableHead>
                    <TableHead>Due</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tenantInvoices.map(invoice => (
                    <TableRow key={invoice.id}>
                      <TableCell className="font-medium">{invoice.invoiceNumber}</TableCell>
                      <TableCell>{invoice.periodMonth}</TableCell>
                      <TableCell>{new Date(invoice.dueDate).toLocaleDateString()}</TableCell>
                      <TableCell>
                        {invoice.status === 'PAID' && <Badge className="bg-green-500">Paid</Badge>}
                        {invoice.status === 'PARTIAL' && <Badge className="bg-amber-500">Partial</Badge>}
                        {invoice.status === 'UNPAID' && <Badge variant="destructive">Unpaid</Badge>}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="font-medium">{formatCurrency(invoice.amountDue)}</div>
                        {invoice.amountPaid > 0 && <div className="text-xs text-muted-foreground">Paid: {formatCurrency(invoice.amountPaid)}</div>}
                      </TableCell>
                    </TableRow>
                  ))}
                  {tenantInvoices.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-4 text-muted-foreground">No invoices found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}