import { useListAllUnits, getListAllUnitsQueryKey } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";

export default function Units() {
  const { data: units, isLoading } = useListAllUnits(undefined, { 
    query: { queryKey: getListAllUnitsQueryKey() } 
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "VACANT": return <Badge className="bg-green-500 hover:bg-green-600">Vacant</Badge>;
      case "OCCUPIED": return <Badge className="bg-blue-500 hover:bg-blue-600">Occupied</Badge>;
      case "MAINTENANCE": return <Badge variant="destructive" className="bg-amber-500 hover:bg-amber-600">Maintenance</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">All Units</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Directory</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">Loading units...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Property</TableHead>
                  <TableHead>Unit Number</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Rent</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Tenant</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {units?.map(unit => (
                  <TableRow key={unit.id}>
                    <TableCell className="font-medium">{unit.propertyName}</TableCell>
                    <TableCell>{unit.unitNumber}</TableCell>
                    <TableCell>{unit.unitType}</TableCell>
                    <TableCell>{formatCurrency(unit.monthlyRent)}</TableCell>
                    <TableCell>{getStatusBadge(unit.status)}</TableCell>
                    <TableCell className="text-muted-foreground">{unit.currentTenantName || '-'}</TableCell>
                  </TableRow>
                ))}
                {units?.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground border-dashed">No units found.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}