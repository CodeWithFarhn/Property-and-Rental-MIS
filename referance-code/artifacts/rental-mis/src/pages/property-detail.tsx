import { useState } from "react";
import { useParams, Link } from "wouter";
import { 
  useGetProperty,
  useListUnits,
  useCreateUnit,
  getGetPropertyQueryKey,
  getListUnitsQueryKey
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Building2, MapPin, Plus, ArrowLeft } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { useAuth } from "../contexts/auth-context";

const unitSchema = z.object({
  unitNumber: z.string().min(1),
  unitType: z.enum(["APARTMENT", "SHOP", "STUDIO", "HOUSE", "OTHER"]),
  bedrooms: z.coerce.number().min(0),
  monthlyRent: z.coerce.number().min(0),
  status: z.enum(["VACANT", "OCCUPIED", "MAINTENANCE"]).default("VACANT"),
});

export default function PropertyDetail() {
  const { id } = useParams<{ id: string }>();
  const propertyId = Number(id);
  const { user } = useAuth();
  
  const { data: property, isLoading: loadingProperty } = useGetProperty(propertyId, { 
    query: { enabled: !!propertyId, queryKey: getGetPropertyQueryKey(propertyId) } 
  });
  
  const { data: units, isLoading: loadingUnits } = useListUnits(propertyId, {
    query: { enabled: !!propertyId, queryKey: getListUnitsQueryKey(propertyId) }
  });

  const [isAddOpen, setIsAddOpen] = useState(false);
  const queryClient = useQueryClient();
  const createUnit = useCreateUnit();

  const form = useForm<z.infer<typeof unitSchema>>({
    resolver: zodResolver(unitSchema),
    defaultValues: { unitNumber: "", unitType: "APARTMENT", bedrooms: 0, monthlyRent: 0, status: "VACANT" },
  });

  const onSubmit = async (values: z.infer<typeof unitSchema>) => {
    await createUnit.mutateAsync({ data: { ...values, propertyId } as any });
    await queryClient.invalidateQueries({ queryKey: getListUnitsQueryKey(propertyId) });
    await queryClient.invalidateQueries({ queryKey: getGetPropertyQueryKey(propertyId) });
    setIsAddOpen(false);
    form.reset();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "VACANT": return <Badge className="bg-green-500 hover:bg-green-600">Vacant</Badge>;
      case "OCCUPIED": return <Badge className="bg-blue-500 hover:bg-blue-600">Occupied</Badge>;
      case "MAINTENANCE": return <Badge variant="destructive" className="bg-amber-500 hover:bg-amber-600">Maintenance</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  const canAdd = user?.role === "ADMIN" || user?.role === "MANAGER";

  if (loadingProperty) return <div>Loading...</div>;
  if (!property) return <div>Property not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" asChild>
          <Link href="/properties"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">{property.name}</h1>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Property Details</CardTitle>
            <CardDescription className="flex items-center gap-1 mt-2">
              <MapPin className="h-4 w-4" /> {property.address}, {property.location}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Owner</span>
                <span className="font-medium">{property.ownerName || 'Unknown'}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Total Units</span>
                <span className="font-medium">{property.totalUnits}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground text-green-600">Vacant</span>
                <span className="font-medium">{property.vacantUnits}</span>
              </div>
              <div className="flex justify-between pb-2">
                <span className="text-muted-foreground text-blue-600">Occupied</span>
                <span className="font-medium">{property.occupiedUnits}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Units</CardTitle>
            {canAdd && (
              <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                <DialogTrigger asChild>
                  <Button size="sm"><Plus className="mr-2 h-4 w-4" /> Add Unit</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Unit</DialogTitle>
                  </DialogHeader>
                  <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <FormField control={form.control} name="unitNumber" render={({ field }) => (
                          <FormItem>
                            <FormLabel>Unit Number</FormLabel>
                            <FormControl><Input placeholder="e.g. A-101" {...field} /></FormControl>
                            <FormMessage />
                          </FormItem>
                        )} />
                        <FormField control={form.control} name="unitType" render={({ field }) => (
                          <FormItem>
                            <FormLabel>Type</FormLabel>
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                              <FormControl><SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger></FormControl>
                              <SelectContent>
                                <SelectItem value="APARTMENT">Apartment</SelectItem>
                                <SelectItem value="SHOP">Shop</SelectItem>
                                <SelectItem value="STUDIO">Studio</SelectItem>
                                <SelectItem value="HOUSE">House</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )} />
                        <FormField control={form.control} name="bedrooms" render={({ field }) => (
                          <FormItem>
                            <FormLabel>Bedrooms/Rooms</FormLabel>
                            <FormControl><Input type="number" {...field} /></FormControl>
                            <FormMessage />
                          </FormItem>
                        )} />
                        <FormField control={form.control} name="monthlyRent" render={({ field }) => (
                          <FormItem>
                            <FormLabel>Monthly Rent (PKR)</FormLabel>
                            <FormControl><Input type="number" {...field} /></FormControl>
                            <FormMessage />
                          </FormItem>
                        )} />
                      </div>
                      <DialogFooter>
                        <Button type="submit" disabled={createUnit.isPending}>Save Unit</Button>
                      </DialogFooter>
                    </form>
                  </Form>
                </DialogContent>
              </Dialog>
            )}
          </CardHeader>
          <CardContent>
            {loadingUnits ? (
              <div className="py-4 text-center">Loading units...</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Unit</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Rent</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Tenant</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {units?.map(unit => (
                    <TableRow key={unit.id}>
                      <TableCell className="font-medium">{unit.unitNumber}</TableCell>
                      <TableCell>{unit.unitType}</TableCell>
                      <TableCell>{formatCurrency(unit.monthlyRent)}</TableCell>
                      <TableCell>{getStatusBadge(unit.status)}</TableCell>
                      <TableCell className="text-muted-foreground">{unit.currentTenantName || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {units?.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-6 text-muted-foreground">No units found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}