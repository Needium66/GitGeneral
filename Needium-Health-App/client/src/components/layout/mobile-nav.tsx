import { useLocation, useRouter } from "wouter";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const navItems = [
  { path: "/", label: "Dashboard", value: "dashboard" },
  { path: "/appointments", label: "Appointments", value: "appointments" },
  { path: "/doctors", label: "Find Doctors", value: "doctors" },
  { path: "/telemedicine", label: "Telemedicine", value: "telemedicine" },
  { path: "/pharmacy", label: "Pharmacy", value: "pharmacy" },
  { path: "/payments", label: "Payments", value: "payments" },
];

export default function MobileNav() {
  const [location] = useLocation();
  const router = useRouter();

  const currentItem = navItems.find(item => item.path === location);

  const handleValueChange = (value: string) => {
    const item = navItems.find(nav => nav.value === value);
    if (item) {
      router(item.path);
    }
  };

  return (
    <div className="md:hidden bg-white border-b border-slate-200">
      <div className="px-4 py-2">
        <Select value={currentItem?.value || "dashboard"} onValueChange={handleValueChange}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select a page" />
          </SelectTrigger>
          <SelectContent>
            {navItems.map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
