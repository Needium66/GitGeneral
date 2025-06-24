import { Heart, Bell } from "lucide-react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const navItems = [
  { path: "/", label: "Dashboard", id: "dashboard" },
  { path: "/appointments", label: "Appointments", id: "appointments" },
  { path: "/doctors", label: "Find Doctors", id: "doctors" },
  { path: "/telemedicine", label: "Telemedicine", id: "telemedicine" },
  { path: "/pharmacy", label: "Pharmacy", id: "pharmacy" },
  { path: "/payments", label: "Payments", id: "payments" },
];

export default function Header() {
  const [location] = useLocation();

  return (
    <header className="bg-white shadow-sm border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-medical-blue rounded-lg flex items-center justify-center">
                <Heart className="text-white h-4 w-4" />
              </div>
              <h1 className="text-xl font-bold text-slate-900">NINC Health</h1>
            </Link>
            <nav className="hidden md:flex space-x-6">
              {navItems.map((item) => (
                <Link key={item.id} href={item.path}>
                  <Button
                    variant="ghost"
                    className={`text-sm font-medium ${
                      location === item.path
                        ? "text-medical-blue"
                        : "text-slate-600 hover:text-medical-blue"
                    }`}
                  >
                    {item.label}
                  </Button>
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="icon">
              <Bell className="h-5 w-5 text-slate-600" />
            </Button>
            <div className="flex items-center space-x-2">
              <Avatar className="h-8 w-8">
                <AvatarImage src="https://images.unsplash.com/photo-1559839734-2b71ea197ec2?ixlib=rb-4.0.3&w=40&h=40&fit=crop&crop=face" />
                <AvatarFallback>SJ</AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium text-slate-700">Sarah Johnson</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
