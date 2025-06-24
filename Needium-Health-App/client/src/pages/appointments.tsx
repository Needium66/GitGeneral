import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Calendar, Clock, Plus, ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertAppointmentSchema } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { formatDate, formatTime } from "@/lib/utils";

const CURRENT_USER_ID = 1;

export default function Appointments() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: appointments = [] } = useQuery({
    queryKey: [`/api/appointments/user/${CURRENT_USER_ID}`],
  });

  const { data: doctors = [] } = useQuery({
    queryKey: ["/api/doctors"],
  });

  const form = useForm({
    resolver: zodResolver(insertAppointmentSchema),
    defaultValues: {
      userId: CURRENT_USER_ID,
      doctorId: 0,
      appointmentDate: "",
      appointmentTime: "",
      appointmentType: "in-person",
      status: "scheduled",
      notes: "",
    },
  });

  const createAppointmentMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiRequest("POST", "/api/appointments", data);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [`/api/appointments/user/${CURRENT_USER_ID}`] });
      setIsDialogOpen(false);
      form.reset();
      toast({
        title: "Success",
        description: "Appointment booked successfully",
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to book appointment",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: any) => {
    createAppointmentMutation.mutate(data);
  };

  const upcomingAppointments = appointments.filter((apt: any) => 
    apt.status === "scheduled" || apt.status === "confirmed"
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed": return "bg-medical-blue/10 text-medical-blue";
      case "scheduled": return "bg-healthcare-green/10 text-healthcare-green";
      case "completed": return "bg-slate-100 text-slate-600";
      case "cancelled": return "bg-red-100 text-red-600";
      default: return "bg-slate-100 text-slate-600";
    }
  };

  const getDoctorName = (doctorId: number) => {
    const doctor = doctors.find((d: any) => d.id === doctorId);
    return doctor ? `Dr. ${doctor.firstName} ${doctor.lastName}` : "Unknown Doctor";
  };

  const getDoctorSpecialty = (doctorId: number) => {
    const doctor = doctors.find((d: any) => d.id === doctorId);
    return doctor ? doctor.specialty : "";
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-900 mb-2">Appointments</h2>
            <p className="text-slate-600">Schedule and manage your medical appointments.</p>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-medical-blue hover:bg-blue-700">
                <Plus className="mr-2 h-4 w-4" />
                Book New Appointment
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Book New Appointment</DialogTitle>
              </DialogHeader>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="doctorId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Doctor</FormLabel>
                        <Select onValueChange={(value) => field.onChange(parseInt(value))} value={field.value.toString()}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select a doctor" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {doctors.map((doctor: any) => (
                              <SelectItem key={doctor.id} value={doctor.id.toString()}>
                                Dr. {doctor.firstName} {doctor.lastName} - {doctor.specialty}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="appointmentDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Date</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="appointmentTime"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Time</FormLabel>
                        <FormControl>
                          <Input type="time" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="appointmentType"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Type</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select appointment type" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="in-person">In-Person</SelectItem>
                            <SelectItem value="telemedicine">Telemedicine</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="notes"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Notes (Optional)</FormLabel>
                        <FormControl>
                          <Textarea placeholder="Any additional notes..." {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button 
                    type="submit" 
                    className="w-full bg-medical-blue hover:bg-blue-700"
                    disabled={createAppointmentMutation.isPending}
                  >
                    {createAppointmentMutation.isPending ? "Booking..." : "Book Appointment"}
                  </Button>
                </form>
              </Form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Calendar */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>December 2024</CardTitle>
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="icon">
                    <ChevronLeft className="h-4 w-4 text-slate-600" />
                  </Button>
                  <Button variant="ghost" size="icon">
                    <ChevronRight className="h-4 w-4 text-slate-600" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-7 gap-2 mb-4">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                  <div key={day} className="text-center text-xs font-medium text-slate-600 py-2">
                    {day}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-2">
                {Array.from({ length: 35 }, (_, i) => {
                  const day = i - 3; // Start from Nov 27
                  const isCurrentMonth = day > 0 && day <= 31;
                  const hasAppointment = [14, 15, 21].includes(day);
                  
                  return (
                    <div
                      key={i}
                      className={`text-center py-3 text-sm ${
                        !isCurrentMonth
                          ? "text-slate-400"
                          : hasAppointment
                          ? day === 14
                            ? "bg-medical-blue text-white rounded-lg font-medium"
                            : day === 15
                            ? "bg-medical-blue/10 text-medical-blue rounded-lg font-medium"
                            : "bg-healthcare-green/10 text-healthcare-green rounded-lg font-medium"
                          : "text-slate-900 hover:bg-slate-100 rounded-lg cursor-pointer"
                      }`}
                    >
                      {isCurrentMonth ? day : day <= 0 ? 27 + day : day - 31}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Upcoming Appointments */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Appointments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {upcomingAppointments.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                  <p className="text-slate-500 text-sm">No upcoming appointments</p>
                  <p className="text-slate-400 text-xs">Book your first appointment to get started</p>
                </div>
              ) : (
                upcomingAppointments.map((appointment: any) => (
                  <div key={appointment.id} className="border border-slate-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-slate-900">
                        {getDoctorName(appointment.doctorId)}
                      </h4>
                      <Badge className={getStatusColor(appointment.status)}>
                        {appointment.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-600 mb-2">
                      {getDoctorSpecialty(appointment.doctorId)}
                    </p>
                    <div className="flex items-center text-xs text-slate-500 space-x-4">
                      <span>
                        <Calendar className="inline mr-1 h-3 w-3" />
                        {formatDate(appointment.appointmentDate)}
                      </span>
                      <span>
                        <Clock className="inline mr-1 h-3 w-3" />
                        {formatTime(appointment.appointmentTime)}
                      </span>
                    </div>
                  </div>
                ))
              )}
              <Button variant="ghost" className="w-full text-medical-blue hover:bg-medical-blue/5">
                View All Appointments
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
