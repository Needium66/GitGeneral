import { 
  users, doctors, appointments, prescriptions, pharmacies, payments, paymentMethods,
  type User, type InsertUser, type Doctor, type InsertDoctor, 
  type Appointment, type InsertAppointment, type Prescription, type InsertPrescription,
  type Pharmacy, type InsertPharmacy, type Payment, type InsertPayment,
  type PaymentMethod, type InsertPaymentMethod
} from "@shared/schema";

export interface IStorage {
  // Users
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  updateUser(id: number, user: Partial<InsertUser>): Promise<User | undefined>;

  // Doctors
  getAllDoctors(): Promise<Doctor[]>;
  getDoctor(id: number): Promise<Doctor | undefined>;
  searchDoctors(specialty?: string, location?: string): Promise<Doctor[]>;
  createDoctor(doctor: InsertDoctor): Promise<Doctor>;

  // Appointments
  getUserAppointments(userId: number): Promise<Appointment[]>;
  getDoctorAppointments(doctorId: number): Promise<Appointment[]>;
  getAppointment(id: number): Promise<Appointment | undefined>;
  createAppointment(appointment: InsertAppointment): Promise<Appointment>;
  updateAppointment(id: number, appointment: Partial<InsertAppointment>): Promise<Appointment | undefined>;

  // Prescriptions
  getUserPrescriptions(userId: number): Promise<Prescription[]>;
  getPrescription(id: number): Promise<Prescription | undefined>;
  createPrescription(prescription: InsertPrescription): Promise<Prescription>;
  updatePrescription(id: number, prescription: Partial<InsertPrescription>): Promise<Prescription | undefined>;

  // Pharmacies
  getAllPharmacies(): Promise<Pharmacy[]>;
  getNearbyPharmacies(zipCode: string): Promise<Pharmacy[]>;

  // Payments
  getUserPayments(userId: number): Promise<Payment[]>;
  getPayment(id: number): Promise<Payment | undefined>;
  createPayment(payment: InsertPayment): Promise<Payment>;
  updatePayment(id: number, payment: Partial<InsertPayment>): Promise<Payment | undefined>;

  // Payment Methods
  getUserPaymentMethods(userId: number): Promise<PaymentMethod[]>;
  createPaymentMethod(paymentMethod: InsertPaymentMethod): Promise<PaymentMethod>;
  updatePaymentMethod(id: number, paymentMethod: Partial<InsertPaymentMethod>): Promise<PaymentMethod | undefined>;
  deletePaymentMethod(id: number): Promise<boolean>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private doctors: Map<number, Doctor>;
  private appointments: Map<number, Appointment>;
  private prescriptions: Map<number, Prescription>;
  private pharmacies: Map<number, Pharmacy>;
  private payments: Map<number, Payment>;
  private paymentMethods: Map<number, PaymentMethod>;
  
  private currentUserId: number;
  private currentDoctorId: number;
  private currentAppointmentId: number;
  private currentPrescriptionId: number;
  private currentPharmacyId: number;
  private currentPaymentId: number;
  private currentPaymentMethodId: number;

  constructor() {
    this.users = new Map();
    this.doctors = new Map();
    this.appointments = new Map();
    this.prescriptions = new Map();
    this.pharmacies = new Map();
    this.payments = new Map();
    this.paymentMethods = new Map();
    
    this.currentUserId = 1;
    this.currentDoctorId = 1;
    this.currentAppointmentId = 1;
    this.currentPrescriptionId = 1;
    this.currentPharmacyId = 1;
    this.currentPaymentId = 1;
    this.currentPaymentMethodId = 1;

    this.seedData();
  }

  private seedData() {
    // Seed sample doctors
    const sampleDoctors: InsertDoctor[] = [
      {
        firstName: "Sarah",
        lastName: "Wilson",
        specialty: "Cardiology",
        email: "s.wilson@hospital.com",
        phone: "(555) 123-4567",
        address: "123 Medical Center Dr",
        city: "Healthcare City",
        state: "HC",
        zipCode: "12345",
        consultationFee: "200.00",
        rating: "4.9",
        reviewCount: 127,
        availability: ["today", "tomorrow"],
        imageUrl: "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?ixlib=rb-4.0.3&w=100&h=100&fit=crop&crop=face"
      },
      {
        firstName: "Michael",
        lastName: "Chen",
        specialty: "Family Medicine",
        email: "m.chen@clinic.com",
        phone: "(555) 234-5678",
        address: "456 Riverside Ave",
        city: "Healthcare City",
        state: "HC",
        zipCode: "12345",
        consultationFee: "150.00",
        rating: "4.7",
        reviewCount: 89,
        availability: ["tomorrow", "this_week"],
        imageUrl: "https://images.unsplash.com/photo-1582750433449-648ed127bb54?ixlib=rb-4.0.3&w=100&h=100&fit=crop&crop=face"
      },
      {
        firstName: "Emily",
        lastName: "Rodriguez",
        specialty: "Pediatrics",
        email: "e.rodriguez@children.com",
        phone: "(555) 345-6789",
        address: "789 Children's Way",
        city: "Healthcare City",
        state: "HC",
        zipCode: "12345",
        consultationFee: "180.00",
        rating: "5.0",
        reviewCount: 156,
        availability: ["this_week"],
        imageUrl: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?ixlib=rb-4.0.3&w=100&h=100&fit=crop&crop=face"
      }
    ];

    sampleDoctors.forEach(doctor => {
      const id = this.currentDoctorId++;
      this.doctors.set(id, { ...doctor, id, createdAt: new Date() });
    });

    // Seed sample pharmacies
    const samplePharmacies: InsertPharmacy[] = [
      {
        name: "CVS Pharmacy",
        address: "123 Main Street",
        city: "Healthcare City",
        state: "HC",
        zipCode: "12345",
        phone: "(555) 123-4567",
        hours: "Open until 10 PM",
        distance: "0.8"
      },
      {
        name: "Walgreens",
        address: "456 Oak Avenue",
        city: "Healthcare City",
        state: "HC",
        zipCode: "12345",
        phone: "(555) 234-5678",
        hours: "Open 24 hours",
        distance: "1.2"
      }
    ];

    samplePharmacies.forEach(pharmacy => {
      const id = this.currentPharmacyId++;
      this.pharmacies.set(id, { ...pharmacy, id });
    });
  }

  // Users
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(user => user.username === username);
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.currentUserId++;
    const user: User = { ...insertUser, id, createdAt: new Date() };
    this.users.set(id, user);
    return user;
  }

  async updateUser(id: number, updates: Partial<InsertUser>): Promise<User | undefined> {
    const user = this.users.get(id);
    if (!user) return undefined;
    
    const updatedUser = { ...user, ...updates };
    this.users.set(id, updatedUser);
    return updatedUser;
  }

  // Doctors
  async getAllDoctors(): Promise<Doctor[]> {
    return Array.from(this.doctors.values());
  }

  async getDoctor(id: number): Promise<Doctor | undefined> {
    return this.doctors.get(id);
  }

  async searchDoctors(specialty?: string, location?: string): Promise<Doctor[]> {
    let doctors = Array.from(this.doctors.values());
    
    if (specialty && specialty !== "All Specialties") {
      doctors = doctors.filter(doctor => 
        doctor.specialty.toLowerCase().includes(specialty.toLowerCase())
      );
    }
    
    if (location) {
      doctors = doctors.filter(doctor => 
        doctor.city.toLowerCase().includes(location.toLowerCase()) ||
        doctor.zipCode.includes(location)
      );
    }
    
    return doctors;
  }

  async createDoctor(insertDoctor: InsertDoctor): Promise<Doctor> {
    const id = this.currentDoctorId++;
    const doctor: Doctor = { 
      ...insertDoctor, 
      id, 
      createdAt: new Date(),
      rating: "0",
      reviewCount: 0
    };
    this.doctors.set(id, doctor);
    return doctor;
  }

  // Appointments
  async getUserAppointments(userId: number): Promise<Appointment[]> {
    return Array.from(this.appointments.values()).filter(
      appointment => appointment.userId === userId
    );
  }

  async getDoctorAppointments(doctorId: number): Promise<Appointment[]> {
    return Array.from(this.appointments.values()).filter(
      appointment => appointment.doctorId === doctorId
    );
  }

  async getAppointment(id: number): Promise<Appointment | undefined> {
    return this.appointments.get(id);
  }

  async createAppointment(insertAppointment: InsertAppointment): Promise<Appointment> {
    const id = this.currentAppointmentId++;
    const appointment: Appointment = { 
      ...insertAppointment, 
      id, 
      createdAt: new Date()
    };
    this.appointments.set(id, appointment);
    return appointment;
  }

  async updateAppointment(id: number, updates: Partial<InsertAppointment>): Promise<Appointment | undefined> {
    const appointment = this.appointments.get(id);
    if (!appointment) return undefined;
    
    const updatedAppointment = { ...appointment, ...updates };
    this.appointments.set(id, updatedAppointment);
    return updatedAppointment;
  }

  // Prescriptions
  async getUserPrescriptions(userId: number): Promise<Prescription[]> {
    return Array.from(this.prescriptions.values()).filter(
      prescription => prescription.userId === userId
    );
  }

  async getPrescription(id: number): Promise<Prescription | undefined> {
    return this.prescriptions.get(id);
  }

  async createPrescription(insertPrescription: InsertPrescription): Promise<Prescription> {
    const id = this.currentPrescriptionId++;
    const prescription: Prescription = { 
      ...insertPrescription, 
      id, 
      createdAt: new Date()
    };
    this.prescriptions.set(id, prescription);
    return prescription;
  }

  async updatePrescription(id: number, updates: Partial<InsertPrescription>): Promise<Prescription | undefined> {
    const prescription = this.prescriptions.get(id);
    if (!prescription) return undefined;
    
    const updatedPrescription = { ...prescription, ...updates };
    this.prescriptions.set(id, updatedPrescription);
    return updatedPrescription;
  }

  // Pharmacies
  async getAllPharmacies(): Promise<Pharmacy[]> {
    return Array.from(this.pharmacies.values());
  }

  async getNearbyPharmacies(zipCode: string): Promise<Pharmacy[]> {
    return Array.from(this.pharmacies.values()).filter(
      pharmacy => pharmacy.zipCode === zipCode
    );
  }

  // Payments
  async getUserPayments(userId: number): Promise<Payment[]> {
    return Array.from(this.payments.values()).filter(
      payment => payment.userId === userId
    );
  }

  async getPayment(id: number): Promise<Payment | undefined> {
    return this.payments.get(id);
  }

  async createPayment(insertPayment: InsertPayment): Promise<Payment> {
    const id = this.currentPaymentId++;
    const payment: Payment = { 
      ...insertPayment, 
      id, 
      createdAt: new Date()
    };
    this.payments.set(id, payment);
    return payment;
  }

  async updatePayment(id: number, updates: Partial<InsertPayment>): Promise<Payment | undefined> {
    const payment = this.payments.get(id);
    if (!payment) return undefined;
    
    const updatedPayment = { ...payment, ...updates };
    this.payments.set(id, updatedPayment);
    return updatedPayment;
  }

  // Payment Methods
  async getUserPaymentMethods(userId: number): Promise<PaymentMethod[]> {
    return Array.from(this.paymentMethods.values()).filter(
      method => method.userId === userId
    );
  }

  async createPaymentMethod(insertPaymentMethod: InsertPaymentMethod): Promise<PaymentMethod> {
    const id = this.currentPaymentMethodId++;
    const paymentMethod: PaymentMethod = { 
      ...insertPaymentMethod, 
      id, 
      createdAt: new Date()
    };
    this.paymentMethods.set(id, paymentMethod);
    return paymentMethod;
  }

  async updatePaymentMethod(id: number, updates: Partial<InsertPaymentMethod>): Promise<PaymentMethod | undefined> {
    const paymentMethod = this.paymentMethods.get(id);
    if (!paymentMethod) return undefined;
    
    const updatedPaymentMethod = { ...paymentMethod, ...updates };
    this.paymentMethods.set(id, updatedPaymentMethod);
    return updatedPaymentMethod;
  }

  async deletePaymentMethod(id: number): Promise<boolean> {
    return this.paymentMethods.delete(id);
  }
}

export const storage = new MemStorage();
