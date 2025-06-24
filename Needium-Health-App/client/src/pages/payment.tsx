import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CreditCard, Plus, Check, Eye, MoreVertical } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertPaymentMethodSchema } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { formatCurrency, formatDate } from "@/lib/utils";

const CURRENT_USER_ID = 1;

export default function Payments() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: payments = [] } = useQuery({
    queryKey: [`/api/payments/user/${CURRENT_USER_ID}`],
  });

  const { data: paymentMethods = [] } = useQuery({
    queryKey: [`/api/payment-methods/user/${CURRENT_USER_ID}`],
  });

  const form = useForm({
    resolver: zodResolver(insertPaymentMethodSchema),
    defaultValues: {
      userId: CURRENT_USER_ID,
      type: "card",
      cardLast4: "",
      cardType: "",
      expiryMonth: "",
      expiryYear: "",
      isDefault: false,
    },
  });

  const addPaymentMethodMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiRequest("POST", "/api/payment-methods", data);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [`/api/payment-methods/user/${CURRENT_USER_ID}`] });
      setIsDialogOpen(false);
      form.reset();
      toast({
        title: "Success",
        description: "Payment method added successfully",
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to add payment method",
        variant: "destructive",
      });
    },
  });

  const payBillMutation = useMutation({
    mutationFn: async (paymentId: number) => {
      const response = await apiRequest("PUT", `/api/payments/${paymentId}`, {
        status: "paid",
        paidDate: new Date().toISOString().split('T')[0],
        paymentMethod: "card"
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [`/api/payments/user/${CURRENT_USER_ID}`] });
      toast({
        title: "Success",
        description: "Payment processed successfully",
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to process payment",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: any) => {
    addPaymentMethodMutation.mutate(data);
  };

  const recentBills = payments.slice(0, 5);
  const outstandingBalance = payments
    .filter((p: any) => p.status === "pending")
    .reduce((sum: number, p: any) => sum + parseFloat(p.patientResponsibility), 0);

  const thisYearTotal = payments
    .reduce((sum: number, p: any) => sum + parseFloat(p.patientResponsibility), 0);

  const insuranceSaved = payments
    .reduce((sum: number, p: any) => sum + parseFloat(p.insurancePaid || "0"), 0);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "paid": return "bg-green-100 text-green-800";
      case "pending": return "bg-red-100 text-red-800";
      case "overdue": return "bg-red-100 text-red-800";
      default: return "bg-slate-100 text-slate-600";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "paid": return "Paid";
      case "pending": return "Due";
      case "overdue": return "Overdue";
      default: return "Unknown";
    }
  };

  const getCardIcon = (cardType: string) => {
    switch (cardType.toLowerCase()) {
      case "visa": return "💳";
      case "mastercard": return "💳";
      case "amex": return "💳";
      default: return "💳";
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-900 mb-2">Payments & Billing</h2>
        <p className="text-slate-600">Manage your medical bills, payments, and insurance claims.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Recent Bills */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Recent Bills</CardTitle>
                <Button variant="ghost" className="text-medical-blue hover:bg-medical-blue/5">
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentBills.length === 0 ? (
                  <div className="text-center py-8">
                    <CreditCard className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <p className="text-slate-500 text-sm">No bills yet</p>
                    <p className="text-slate-400 text-xs">Bills will appear here after appointments</p>
                  </div>
                ) : (
                  recentBills.map((bill: any) => (
                    <div key={bill.id} className="border border-slate-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-slate-900">{bill.description}</h4>
                          <p className="text-sm text-slate-600">
                            {formatDate(bill.createdAt)}
                          </p>
                        </div>
                        <Badge className={getStatusColor(bill.status)}>
                          {getStatusText(bill.status)}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                        <div>
                          <span className="text-slate-600">Total Amount:</span>
                          <p className="font-semibold text-slate-900">
                            {formatCurrency(bill.totalAmount)}
                          </p>
                        </div>
                        <div>
                          <span className="text-slate-600">Insurance Paid:</span>
                          <p className="font-medium text-green-600">
                            {formatCurrency(bill.insurancePaid)}
                          </p>
                        </div>
                        <div>
                          <span className="text-slate-600">Your Responsibility:</span>
                          <p className={`font-semibold ${bill.status === "pending" ? "text-red-600" : "text-green-600"}`}>
                            {formatCurrency(bill.patientResponsibility)}
                          </p>
                        </div>
                        <div>
                          <span className="text-slate-600">Due Date:</span>
                          <p className="font-medium">{formatDate(bill.dueDate)}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                        <Button variant="ghost" className="text-medical-blue hover:bg-medical-blue/5">
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </Button>
                        {bill.status === "pending" ? (
                          <Button 
                            className="bg-medical-blue hover:bg-blue-700"
                            onClick={() => payBillMutation.mutate(bill.id)}
                            disabled={payBillMutation.isPending}
                          >
                            {payBillMutation.isPending ? "Processing..." : "Pay Now"}
                          </Button>
                        ) : (
                          <span className="text-sm text-green-600 font-medium">
                            <Check className="inline mr-1 h-4 w-4" />
                            Payment Complete
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Payment Methods */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Payment Methods</CardTitle>
                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="bg-medical-blue hover:bg-blue-700">
                      <Plus className="mr-2 h-4 w-4" />
                      Add New
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Payment Method</DialogTitle>
                    </DialogHeader>
                    <Form {...form}>
                      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                          control={form.control}
                          name="cardLast4"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Card Number (Last 4 digits)</FormLabel>
                              <FormControl>
                                <Input placeholder="4242" maxLength={4} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="cardType"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Card Type</FormLabel>
                              <Select onValueChange={field.onChange} value={field.value}>
                                <FormControl>
                                  <SelectTrigger>
                                    <SelectValue placeholder="Select card type" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  <SelectItem value="visa">Visa</SelectItem>
                                  <SelectItem value="mastercard">Mastercard</SelectItem>
                                  <SelectItem value="amex">American Express</SelectItem>
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <div className="grid grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="expiryMonth"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Expiry Month</FormLabel>
                                <FormControl>
                                  <Input placeholder="12" maxLength={2} {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name="expiryYear"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Expiry Year</FormLabel>
                                <FormControl>
                                  <Input placeholder="25" maxLength={2} {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>

                        <FormField
                          control={form.control}
                          name="isDefault"
                          render={({ field }) => (
                            <FormItem className="flex items-center justify-between">
                              <FormLabel>Set as default payment method</FormLabel>
                              <FormControl>
                                <Switch
                                  checked={field.value}
                                  onCheckedChange={field.onChange}
                                />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <Button 
                          type="submit" 
                          className="w-full bg-medical-blue hover:bg-blue-700"
                          disabled={addPaymentMethodMutation.isPending}
                        >
                          {addPaymentMethodMutation.isPending ? "Adding..." : "Add Payment Method"}
                        </Button>
                      </form>
                    </Form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {paymentMethods.length === 0 ? (
                  <div className="text-center py-8">
                    <CreditCard className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <p className="text-slate-500 text-sm">No payment methods added</p>
                    <p className="text-slate-400 text-xs">Add a payment method to get started</p>
                  </div>
                ) : (
                  paymentMethods.map((method: any) => (
                    <div key={method.id} className="flex items-center justify-between p-4 border border-slate-200 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="bg-blue-100 p-3 rounded-lg">
                          <CreditCard className="text-blue-600 h-5 w-5" />
                        </div>
                        <div>
                          <h4 className="font-medium text-slate-900">
                            {method.cardType} •••• {method.cardLast4}
                          </h4>
                          <p className="text-sm text-slate-600">
                            Expires {method.expiryMonth}/{method.expiryYear}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {method.isDefault && (
                          <Badge className="bg-green-100 text-green-800">Default</Badge>
                        )}
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="h-4 w-4 text-slate-400" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Account Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <p className="text-sm text-slate-600">Outstanding Balance</p>
                  <p className="text-2xl font-bold text-red-600">
                    {formatCurrency(outstandingBalance)}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-600">This Year</p>
                    <p className="font-semibold text-slate-900">
                      {formatCurrency(thisYearTotal)}
                    </p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-600">Insurance Saved</p>
                    <p className="font-semibold text-green-600">
                      {formatCurrency(insuranceSaved)}
                    </p>
                  </div>
                </div>
              </div>
              {outstandingBalance > 0 && (
                <Button className="w-full mt-4 bg-medical-blue hover:bg-blue-700">
                  Pay Outstanding Balance
                </Button>
              )}
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
                  <span className="text-slate-600">Policy Number:</span>
                  <p className="font-medium">BC123456789</p>
                </div>
                <div>
                  <span className="text-slate-600">Deductible:</span>
                  <p className="font-medium">$500 (Met: $350)</p>
                </div>
                <div>
                  <span className="text-slate-600">Out-of-Pocket Max:</span>
                  <p className="font-medium">$2,000 (Used: $450)</p>
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
              <CardTitle>Payment Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-700">Auto-pay</span>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-700">Email receipts</span>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-700">Payment reminders</span>
                  <Switch />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
