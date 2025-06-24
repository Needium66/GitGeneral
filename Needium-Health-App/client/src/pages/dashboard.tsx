import { useQuery } from "@tanstack/react-query";
import { Calendar, Pills, Vial, Heart, UserMd, PrescriptionBottle, Video, Search } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRouter } from "wouter";

// Mock user ID for demonstration - in a real app this would come from auth
const CURRENT_USER_ID = 1;

export default function Dashboard() {
  const router = useRouter();

  const { data: appointments = [] } = useQuery({
    queryKey: [`/api/appointments/user/${CURRENT_USER_ID}`],
  });

  const { data: prescriptions = [] } = useQuery({
    queryKey: [`/api/prescriptions/user/${CURRENT_USER_ID}`],
  });

  const { data: payments = [] } = useQuery({
    queryKey: [`/api/payments/user/${CURRENT_USER_ID}`],
  });

  const upcomingAppointments = appointments.filter((apt: any) => apt.status === "scheduled").length;
  const activePrescriptions = prescriptions.filter((rx: any) => rx.status === "active").length;
  const pendingPayments = payments.filter((payment: any) => payment.status === "pending").length;

  const quickActions = [
    {
      title: "Book Appointment",
      icon: Calendar,
      color: "bg-medical-blue/5 hover:bg-medical-blue/10",
      iconColor: "text-medical-blue",
      action: () => router("/appointments"),
    },
    {
      title: "Refill Prescription",
      icon: Pills,
      color: "bg-healthcare-green/5 hover:bg-healthcare-green/10",
      iconColor: "text-healthcare-green",
      action: () => router("/pharmacy"),
    },
    {
      title: "Start Video Call",
      icon: Video,
      color: "bg-medical-teal/5 hover:bg-medical-teal/10",
      iconColor: "text-medical-teal",
      action: () => router("/telemedicine"),
    },
    {
      title: "Find Doctor",
      icon: Search,
      color: "bg-purple-50 hover:bg-purple-100",
      iconColor: "text-purple-600",
      action: () => router("/doctors"),
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-900 mb-2">
          Welcome back, Sarah
        </h2>
        <p className="text-slate-600">
          Manage your health appointments, prescriptions, and medical records.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600 text-sm font-medium">Upcoming Appointments</p>
                <p className="text-3xl font-bold text-slate-900">{upcomingAppointments}</p>
              </div>
              <div className="bg-medical-blue/10 p-3 rounded-lg">
                <Calendar className="text-medical-blue h-6 w-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600 text-sm font-medium">Active Prescriptions</p>
                <p className="text-3xl font-bold text-slate-900">{activePrescriptions}</p>
              </div>
              <div className="bg-healthcare-green/10 p-3 rounded-lg">
                <Pills className="text-healthcare-green h-6 w-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600 text-sm font-medium">Pending Payments</p>
                <p className="text-3xl font-bold text-slate-900">{pendingPayments}</p>
              </div>
              <div className="bg-medical-teal/10 p-3 rounded-lg">
                <Vial className="text-medical-teal h-6 w-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600 text-sm font-medium">Health Score</p>
                <p className="text-3xl font-bold text-slate-900">85</p>
              </div>
              <div className="bg-green-100 p-3 rounded-lg">
                <Heart className="text-green-600 h-6 w-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3 pb-4 border-b border-slate-100 last:border-b-0">
                <div className="bg-medical-blue/10 p-2 rounded-lg flex-shrink-0">
                  <UserMd className="text-medical-blue h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-900">No recent appointments</p>
                  <p className="text-xs text-slate-600">Book your first appointment to get started</p>
                  <p className="text-xs text-slate-500">Ready when you are</p>
                </div>
              </div>

              <div className="flex items-start space-x-3 pb-4 border-b border-slate-100 last:border-b-0">
                <div className="bg-healthcare-green/10 p-2 rounded-lg flex-shrink-0">
                  <PrescriptionBottle className="text-healthcare-green h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-900">No prescriptions yet</p>
                  <p className="text-xs text-slate-600">Prescriptions will appear here after doctor visits</p>
                  <p className="text-xs text-slate-500">Stay healthy</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="bg-medical-teal/10 p-2 rounded-lg flex-shrink-0">
                  <Vial className="text-medical-teal h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-900">Welcome to NINC Health</p>
                  <p className="text-xs text-slate-600">Your comprehensive healthcare platform</p>
                  <p className="text-xs text-slate-500">Get started today</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {quickActions.map((action, index) => (
                <Button
                  key={index}
                  variant="ghost"
                  className={`flex flex-col items-center p-4 h-auto ${action.color} transition-colors`}
                  onClick={action.action}
                >
                  <action.icon className={`${action.iconColor} h-8 w-8 mb-2`} />
                  <span className="text-sm font-medium text-slate-900">{action.title}</span>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
