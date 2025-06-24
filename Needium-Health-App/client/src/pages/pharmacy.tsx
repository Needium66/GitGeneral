import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Pills, MapPin, Clock, Phone, Car, ExclamationTriangle, History, CreditCard } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

const CURRENT_USER_ID = 1;

export default function Pharmacy() {
  const [searchLocation, setSearchLocation] = useState("");
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: prescriptions = [] } = useQuery({
    queryKey: [`/api/prescriptions/user/${CURRENT_USER_ID}`],
  });

  const { data: pharmacies = [] } = useQuery({
    queryKey: ["/api/pharmacies"],
  });

  const { data: doctors = [] } = useQuery({
    queryKey: ["/api/doctors"],
  });

  const activePrescriptions = prescriptions.filter((rx: any) => rx.status === "active");

  const requestRefillMutation = useMutation({
    mutationFn: async (prescriptionId: number) => {
      const prescription = prescriptions.find((p: any) => p.id === prescriptionId);
      if (!prescription) throw new Error("Prescription not found");
      
      const response = await apiRequest("PUT", `/api/prescriptions/${prescriptionId}`, {
        refillsRemaining: prescription.refillsRemaining - 1,
        status: prescription.refillsRemaining <= 1 ? "refill_due" : "active"
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [`/api/prescriptions/user/${CURRENT_USER_ID}`] });
      toast({
        title: "Success",
        description: "Refill request submitted successfully",
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to request refill",
        variant: "destructive",
      });
    },
  });

  const getDoctorName = (doctorId: number) => {
    const doctor = doctors.find((d: any) => d.id === doctorId);
    return doctor ? `Dr. ${doctor.firstName} ${doctor.lastName}` : "Unknown Doctor";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-100 text-green-800";
      case "refill_due": return "bg-yellow-100 text-yellow-800";
      case "expired": return "bg-red-100 text-red-800";
      default: return "bg-slate-100 text-slate-600";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "active": return "Active";
      case "refill_due": return "Refill Due";
      case "expired": return "Expired";
      default: return "Unknown";
    }
  };

  const isDueForRefill = (prescription: any) => {
    const prescribedDate = new Date(prescription.prescribedDate);
    const daysSincePrescribed = Math.floor((Date.now() - prescribedDate.getTime()) / (1000 * 60 * 60 * 24));
    return daysSincePrescribed > 25; // Mock logic for demonstration
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-900 mb-2">Pharmacy Services</h2>
        <p className="text-slate-600">Manage prescriptions, refills, and find nearby pharmacies.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Active Prescriptions */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Active Prescriptions</CardTitle>
                <Button variant="ghost" className="text-medical-blue hover:bg-medical-blue/5">
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activePrescriptions.length === 0 ? (
                  <div className="text-center py-8">
                    <Pills className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <p className="text-slate-500 text-sm">No active prescriptions</p>
                    <p className="text-slate-400 text-xs">Prescriptions will appear here after doctor visits</p>
                  </div>
                ) : (
                  activePrescriptions.map((prescription: any) => (
                    <div key={prescription.id} className="border border-slate-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-slate-900">{prescription.medicationName}</h4>
                          <p className="text-sm text-slate-600">
                            Prescribed by {getDoctorName(prescription.doctorId)}
                          </p>
                        </div>
                        <Badge className={getStatusColor(prescription.status)}>
                          {getStatusText(prescription.status)}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-slate-600">Dosage:</span>
                          <p className="font-medium">{prescription.dosage}</p>
                        </div>
                        <div>
                          <span className="text-slate-600">Quantity:</span>
                          <p className="font-medium">{prescription.quantity} tablets</p>
                        </div>
                        <div>
                          <span className="text-slate-600">Refills:</span>
                          <p className="font-medium">{prescription.refillsRemaining} remaining</p>
                        </div>
                        <div>
                          <span className="text-slate-600">Expires:</span>
                          <p className="font-medium">{formatDate(prescription.expiryDate)}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
                        <p className="text-sm text-slate-600">
                          {isDueForRefill(prescription) ? (
                            <>
                              <ExclamationTriangle className="inline mr-1 h-4 w-4 text-yellow-500" />
                              Due for refill in 3 days
                            </>
                          ) : (
                            <>
                              <Clock className="inline mr-1 h-4 w-4" />
                              Last filled: {formatDate(prescription.prescribedDate)}
                            </>
                          )}
                        </p>
                        <Button 
                          className="bg-healthcare-green hover:bg-green-700 text-white"
                          onClick={() => requestRefillMutation.mutate(prescription.id)}
                          disabled={requestRefillMutation.isPending || prescription.refillsRemaining <= 0}
                        >
                          {requestRefillMutation.isPending ? "Requesting..." : "Request Refill"}
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Find Pharmacies */}
          <Card>
            <CardHeader>
              <CardTitle>Find Nearby Pharmacies</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex space-x-4 mb-4">
                <div className="flex-1">
                  <Input
                    type="text"
                    placeholder="Enter your address or zip code"
                    value={searchLocation}
                    onChange={(e) => setSearchLocation(e.target.value)}
                  />
                </div>
                <Button className="bg-medical-blue hover:bg-blue-700">
                  Search
                </Button>
              </div>
              
              <div className="space-y-4">
                {pharmacies.map((pharmacy: any) => (
                  <div key={pharmacy.id} className="flex items-start space-x-4 p-4 border border-slate-200 rounded-lg">
                    <div className="bg-healthcare-green/10 p-3 rounded-lg flex-shrink-0">
                      <Pills className="text-healthcare-green h-6 w-6" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-900">{pharmacy.name}</h4>
                      <p className="text-sm text-slate-600 mb-2">
                        {pharmacy.address}, {pharmacy.city}, {pharmacy.state} {pharmacy.zipCode}
                      </p>
                      <div className="flex items-center space-x-4 text-xs text-slate-600">
                        <span>
                          <Clock className="inline mr-1 h-3 w-3" />
                          {pharmacy.hours}
                        </span>
                        <span>
                          <Phone className="inline mr-1 h-3 w-3" />
                          {pharmacy.phone}
                        </span>
                        <span>
                          <Car className="inline mr-1 h-3 w-3" />
                          {pharmacy.distance} miles
                        </span>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      className="text-medical-blue hover:bg-medical-blue/5"
                    >
                      Select
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Button className="w-full bg-medical-blue hover:bg-blue-700">
                  <Pills className="mr-2 h-4 w-4" />
                  Request Refill
                </Button>
                <Button className="w-full bg-healthcare-green hover:bg-green-700">
                  <CreditCard className="mr-2 h-4 w-4" />
                  Transfer Prescription
                </Button>
                <Button variant="outline" className="w-full">
                  <History className="mr-2 h-4 w-4" />
                  Prescription History
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Insurance Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-slate-600">Primary Insurance:</span>
                  <p className="font-medium">Blue Cross Blue Shield</p>
                </div>
                <div>
                  <span className="text-slate-600">Member ID:</span>
                  <p className="font-medium">BC123456789</p>
                </div>
                <div>
                  <span className="text-slate-600">Group Number:</span>
                  <p className="font-medium">GRP001</p>
                </div>
              </div>
              <Button 
                variant="ghost" 
                className="w-full mt-4 text-medical-blue hover:bg-medical-blue/5"
              >
                Update Insurance
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Prescription Reminders</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {activePrescriptions.length === 0 ? (
                  <p className="text-slate-500 text-sm text-center py-4">
                    No active prescriptions to remind
                  </p>
                ) : (
                  activePrescriptions.slice(0, 3).map((prescription: any) => (
                    <div key={prescription.id} className="flex items-center space-x-3 py-2">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-900">
                          {prescription.medicationName}
                        </p>
                        <p className="text-xs text-slate-600">
                          {prescription.instructions || "Take as directed"}
                        </p>
                      </div>
                      <span className="text-xs text-slate-500">Daily</span>
                    </div>
                  ))
                )}
              </div>
              <Button 
                variant="ghost" 
                className="w-full mt-4 text-medical-blue hover:bg-medical-blue/5"
              >
                Manage Reminders
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
