import { useState } from "react";
import { Link } from "wouter";
import { 
  useListProperties, 
  useCreateProperty, 
  getListPropertiesQueryKey 
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Building2, MapPin, Plus } from "lucide-react";
import { useAuth } from "../contexts/auth-context";

const propertySchema = z.object({
  name: z.string().min(1, "Name is required"),
  address: z.string().min(1, "Address is required"),
  location: z.string().min(1, "Location is required"),
  ownerId: z.coerce.number().min(1),
});

export default function Properties() {
  const { data: properties, isLoading } = useListProperties({ query: { queryKey: getListPropertiesQueryKey() } });
  const [isAddOpen, setIsAddOpen] = useState(false);
  const queryClient = useQueryClient();
  const { user } = useAuth();
  
  const createProperty = useCreateProperty();

  const form = useForm<z.infer<typeof propertySchema>>({
    resolver: zodResolver(propertySchema),
    defaultValues: { name: "", address: "", location: "", ownerId: user?.id || 1 },
  });

  const onSubmit = async (values: z.infer<typeof propertySchema>) => {
    await createProperty.mutateAsync({ data: values });
    await queryClient.invalidateQueries({ queryKey: getListPropertiesQueryKey() });
    setIsAddOpen(false);
    form.reset();
  };

  const canAdd = user?.role === "ADMIN" || user?.role === "MANAGER";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Properties</h1>
        {canAdd && (
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button><Plus className="mr-2 h-4 w-4" /> Add Property</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Property</DialogTitle>
              </DialogHeader>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField control={form.control} name="name" render={({ field }) => (
                    <FormItem>
                      <FormLabel>Property Name</FormLabel>
                      <FormControl><Input placeholder="e.g. Al-Falah Heights" {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                  <FormField control={form.control} name="location" render={({ field }) => (
                    <FormItem>
                      <FormLabel>Location</FormLabel>
                      <FormControl><Input placeholder="e.g. Gulberg III, Lahore" {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                  <FormField control={form.control} name="address" render={({ field }) => (
                    <FormItem>
                      <FormLabel>Full Address</FormLabel>
                      <FormControl><Input placeholder="Complete street address" {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                  <DialogFooter>
                    <Button type="submit" disabled={createProperty.isPending}>Save Property</Button>
                  </DialogFooter>
                </form>
              </Form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {isLoading ? (
        <div>Loading properties...</div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {properties?.map(property => (
            <Link key={property.id} href={`/properties/${property.id}`}>
              <Card className="hover:bg-muted/50 cursor-pointer transition-colors h-full flex flex-col">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-primary" />
                    {property.name}
                  </CardTitle>
                  <CardDescription className="flex items-center gap-1">
                    <MapPin className="h-3 w-3" /> {property.location}
                  </CardDescription>
                </CardHeader>
                <CardContent className="mt-auto">
                  <div className="grid grid-cols-3 gap-2 text-center text-sm">
                    <div className="bg-primary/10 rounded-md p-2">
                      <div className="font-semibold text-primary">{property.totalUnits}</div>
                      <div className="text-xs text-muted-foreground">Total</div>
                    </div>
                    <div className="bg-green-500/10 rounded-md p-2">
                      <div className="font-semibold text-green-700">{property.vacantUnits}</div>
                      <div className="text-xs text-muted-foreground">Vacant</div>
                    </div>
                    <div className="bg-blue-500/10 rounded-md p-2">
                      <div className="font-semibold text-blue-700">{property.occupiedUnits}</div>
                      <div className="text-xs text-muted-foreground">Occupied</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
          {properties?.length === 0 && (
            <div className="col-span-full py-12 text-center text-muted-foreground border rounded-lg border-dashed">
              No properties found.
            </div>
          )}
        </div>
      )}
    </div>
  );
}