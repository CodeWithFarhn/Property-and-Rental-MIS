import { Switch, Route, Router as WouterRouter, useLocation } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "./contexts/auth-context";
import { SidebarProvider, Sidebar, SidebarContent, SidebarHeader, SidebarMenu, SidebarMenuItem, SidebarMenuButton } from "@/components/ui/sidebar";
import { Home, Building2, DoorOpen, Users, FileText, FileSpreadsheet, CreditCard, Wrench, ShieldCheck, LogOut } from "lucide-react";
import { Link } from "wouter";

// Pages
import Dashboard from "./pages/dashboard";
import Login from "./pages/login";
import Properties from "./pages/properties";
import PropertyDetail from "./pages/property-detail";
import Units from "./pages/units";
import Tenants from "./pages/tenants";
import TenantDetail from "./pages/tenant-detail";
import Leases from "./pages/leases";
import NewLease from "./pages/new-lease";
import Invoices from "./pages/invoices";
import Payments from "./pages/payments";
import Maintenance from "./pages/maintenance";
import UsersList from "./pages/users";
import NotFound from "./pages/not-found";

const queryClient = new QueryClient();

function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const [location] = useLocation();

  if (!user) return <>{children}</>;

  const navigation = [
    { name: "Dashboard", href: "/", icon: Home, roles: ["ADMIN", "MANAGER", "OWNER"] },
    { name: "Properties", href: "/properties", icon: Building2, roles: ["ADMIN", "MANAGER", "OWNER"] },
    { name: "Units", href: "/units", icon: DoorOpen, roles: ["ADMIN", "MANAGER"] },
    { name: "Tenants", href: "/tenants", icon: Users, roles: ["ADMIN", "MANAGER"] },
    { name: "Leases", href: "/leases", icon: FileText, roles: ["ADMIN", "MANAGER", "TENANT"] },
    { name: "Invoices", href: "/invoices", icon: FileSpreadsheet, roles: ["ADMIN", "MANAGER", "TENANT"] },
    { name: "Payments", href: "/payments", icon: CreditCard, roles: ["ADMIN", "MANAGER", "STAFF", "TENANT"] },
    { name: "Maintenance", href: "/maintenance", icon: Wrench, roles: ["ADMIN", "MANAGER", "STAFF"] },
    { name: "Users", href: "/users", icon: ShieldCheck, roles: ["ADMIN"] },
  ];

  const filteredNav = navigation.filter((item) => item.roles.includes(user.role));

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <Sidebar>
          <SidebarHeader className="p-4">
            <div className="flex flex-col gap-1">
              <span className="font-semibold text-lg">EliteProp MIS</span>
              <span className="text-sm text-muted-foreground">{user.fullName} ({user.role})</span>
            </div>
          </SidebarHeader>
          <SidebarContent>
            <SidebarMenu>
              {filteredNav.map((item) => (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton asChild isActive={location === item.href}>
                    <Link href={item.href} className="flex items-center gap-3">
                      <item.icon className="h-4 w-4" />
                      <span>{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
              <SidebarMenuItem>
                <SidebarMenuButton onClick={logout} className="text-destructive mt-auto">
                  <LogOut className="h-4 w-4" />
                  <span>Logout</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarContent>
        </Sidebar>
        <main className="flex-1 p-6 overflow-y-auto bg-muted/20">
          {children}
        </main>
      </div>
    </SidebarProvider>
  );
}

function ProtectedRoute({ component: Component, roles }: { component: React.ComponentType, roles?: string[] }) {
  const { user, isLoading } = useAuth();
  
  if (isLoading) return <div className="flex h-screen items-center justify-center">Loading...</div>;
  if (!user) return <Login />;
  if (roles && !roles.includes(user.role)) return <div>Unauthorized</div>;

  return <Component />;
}

function Router() {
  return (
    <Layout>
      <Switch>
        <Route path="/login" component={Login} />
        <Route path="/" component={() => <ProtectedRoute component={Dashboard} />} />
        <Route path="/properties" component={() => <ProtectedRoute component={Properties} />} />
        <Route path="/properties/:id" component={() => <ProtectedRoute component={PropertyDetail} />} />
        <Route path="/units" component={() => <ProtectedRoute component={Units} />} />
        <Route path="/tenants" component={() => <ProtectedRoute component={Tenants} />} />
        <Route path="/tenants/:id" component={() => <ProtectedRoute component={TenantDetail} />} />
        <Route path="/leases" component={() => <ProtectedRoute component={Leases} />} />
        <Route path="/leases/new" component={() => <ProtectedRoute component={NewLease} />} />
        <Route path="/invoices" component={() => <ProtectedRoute component={Invoices} />} />
        <Route path="/payments" component={() => <ProtectedRoute component={Payments} />} />
        <Route path="/maintenance" component={() => <ProtectedRoute component={Maintenance} />} />
        <Route path="/users" component={() => <ProtectedRoute component={UsersList} roles={["ADMIN"]} />} />
        <Route component={NotFound} />
      </Switch>
    </Layout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <AuthProvider>
            <Router />
          </AuthProvider>
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
