import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Video, Phone, Mic, Monitor, CheckCircle, ExclamationCircle, Calendar, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { formatTime } from "@/lib/utils";

const CURRENT_USER_ID = 1;

export default function Telemedicine() {
  const [isCallActive, setIsCallActive] = useState(false);
  const [callDuration, setCallDuration] = useState("00:00:00");

  const { data: appointments = [] } = useQuery({
    queryKey: [`/api/appointments/user/${CURRENT_USER_ID}`],
  });

  const { data: doctors = [] } = useQuery({
    queryKey: ["/api/doctors"],
  });

  const telemedicineAppointments = appointments.filter((apt: any) => 
    apt.appointmentType === "telemedicine" && apt.status === "scheduled"
  );

  const upcomingCalls = telemedicineAppointments.slice(0, 3);
  const currentAppointment = telemedicineAppointments[0];

  const getCurrentDoctor = () => {
    if (!currentAppointment) return null;
    return doctors.find((d: any) => d.id === currentAppointment.doctorId);
  };

  const currentDoctor = getCurrentDoctor();

  const handleStartCall = () => {
    setIsCallActive(true);
    // In a real app, this would initialize the video call
  };

  const handleEndCall = () => {
    setIsCallActive(false);
    setCallDuration("00:00:00");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-900 mb-2">Telemedicine</h2>
        <p className="text-slate-600">Connect with healthcare providers through secure video consultations.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Video Call Interface */}
        <div className="lg:col-span-2">
          <div className="bg-slate-900 rounded-xl aspect-video relative overflow-hidden">
            {/* Mock video call interface */}
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
              {isCallActive ? (
                <div className="text-center text-white">
                  <Video className="h-16 w-16 mb-4 mx-auto animate-pulse" />
                  <p className="text-xl font-medium mb-2">Call in Progress</p>
                  <p className="text-slate-400">Connected with {currentDoctor?.firstName} {currentDoctor?.lastName}</p>
                </div>
              ) : (
                <div className="text-center text-white">
                  <Video className="h-16 w-16 mb-4 mx-auto opacity-50" />
                  <p className="text-xl font-medium mb-2">Video Call Not Active</p>
                  <p className="text-slate-400">Click "Start Call" to begin your consultation</p>
                </div>
              )}
            </div>
            
            {/* Video controls */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex items-center space-x-4">
              <Button
                variant="destructive"
                size="icon"
                className="rounded-full"
                onClick={handleEndCall}
                disabled={!isCallActive}
              >
                <Phone className="h-4 w-4" />
              </Button>
              <Button
                variant="secondary"
                size="icon"
                className="rounded-full bg-slate-700 hover:bg-slate-600 text-white"
              >
                <Mic className="h-4 w-4" />
              </Button>
              <Button
                variant="secondary"
                size="icon"
                className="rounded-full bg-slate-700 hover:bg-slate-600 text-white"
              >
                <Video className="h-4 w-4" />
              </Button>
              <Button
                variant="secondary"
                size="icon"
                className="rounded-full bg-slate-700 hover:bg-slate-600 text-white"
              >
                <Monitor className="h-4 w-4" />
              </Button>
            </div>

            {/* Doctor's video (small window) */}
            {currentDoctor && (
              <div className="absolute top-4 right-4 w-32 h-24 bg-slate-800 rounded-lg border-2 border-white overflow-hidden">
                <Avatar className="w-full h-full">
                  <AvatarImage 
                    src={currentDoctor.imageUrl} 
                    alt={`Dr. ${currentDoctor.firstName} ${currentDoctor.lastName}`}
                    className="object-cover"
                  />
                  <AvatarFallback className="text-2xl">
                    {currentDoctor.firstName[0]}{currentDoctor.lastName[0]}
                  </AvatarFallback>
                </Avatar>
              </div>
            )}
          </div>
        </div>

        {/* Call Information & Controls */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Current Consultation</CardTitle>
            </CardHeader>
            <CardContent>
              {currentAppointment && currentDoctor ? (
                <>
                  <div className="flex items-center space-x-3 mb-4">
                    <Avatar className="h-12 w-12">
                      <AvatarImage src={currentDoctor.imageUrl} alt={`Dr. ${currentDoctor.firstName} ${currentDoctor.lastName}`} />
                      <AvatarFallback>
                        {currentDoctor.firstName[0]}{currentDoctor.lastName[0]}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h4 className="font-medium text-slate-900">
                        Dr. {currentDoctor.firstName} {currentDoctor.lastName}
                      </h4>
                      <p className="text-sm text-slate-600">{currentDoctor.specialty}</p>
                    </div>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Appointment Time:</span>
                      <span className="font-medium">
                        {formatTime(currentAppointment.appointmentTime)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Call Duration:</span>
                      <span className="font-medium">{callDuration}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Status:</span>
                      <Badge variant="secondary" className="text-green-600">
                        {isCallActive ? "In Progress" : "Waiting for doctor"}
                      </Badge>
                    </div>
                  </div>
                  <Button 
                    className="w-full mt-4 bg-medical-blue hover:bg-blue-700"
                    onClick={isCallActive ? handleEndCall : handleStartCall}
                  >
                    {isCallActive ? "End Call" : "Start Call"}
                  </Button>
                </>
              ) : (
                <div className="text-center py-8">
                  <Video className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                  <p className="text-slate-500 text-sm">No active telemedicine appointments</p>
                  <p className="text-slate-400 text-xs">Schedule a virtual appointment to get started</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pre-Call Checklist</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-sm text-slate-700">Camera is working</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-sm text-slate-700">Microphone is working</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-sm text-slate-700">Internet connection stable</span>
                </div>
                <div className="flex items-center space-x-3">
                  <ExclamationCircle className="h-5 w-5 text-yellow-500" />
                  <span className="text-sm text-slate-700">Ensure quiet environment</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Upcoming Calls</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {upcomingCalls.length === 0 ? (
                  <div className="text-center py-4">
                    <p className="text-slate-500 text-sm">No upcoming video calls</p>
                  </div>
                ) : (
                  upcomingCalls.map((call: any) => {
                    const doctor = doctors.find((d: any) => d.id === call.doctorId);
                    return (
                      <div key={call.id} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-b-0">
                        <div>
                          <p className="font-medium text-slate-900">
                            Dr. {doctor?.firstName} {doctor?.lastName}
                          </p>
                          <div className="flex items-center text-xs text-slate-600 space-x-2">
                            <Calendar className="h-3 w-3" />
                            <span>{call.appointmentDate}</span>
                            <Clock className="h-3 w-3" />
                            <span>{formatTime(call.appointmentTime)}</span>
                          </div>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="text-medical-blue hover:bg-medical-blue/5"
                        >
                          Join
                        </Button>
                      </div>
                    );
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
