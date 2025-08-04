import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar } from './components/ui/calendar';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Clock, Calendar as CalendarIcon, MapPin, Star, Camera, Video, Palette, Package, Edit3, Image, Users, CheckCircle, Clock as ClockIcon, AlertCircle } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [bookingForm, setBookingForm] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    booking_date: '',
    booking_time: ''
  });
  const [availableSlots, setAvailableSlots] = useState([]);
  const [showBookingDialog, setShowBookingDialog] = useState(false);
  const [currentView, setCurrentView] = useState('home');
  const [customerBookings, setCustomerBookings] = useState([]);
  const [customerEmail, setCustomerEmail] = useState('');
  const [paymentForm, setPaymentForm] = useState({
    booking_id: '',
    payment_amount: '',
    payment_reference: ''
  });
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [showAdminDialog, setShowAdminDialog] = useState(false);
  
  // Admin state
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminForm, setAdminForm] = useState({ username: '', password: '' });
  const [allBookings, setAllBookings] = useState([]);

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API}/services`);
      setServices(response.data);
    } catch (error) {
      console.error('Error fetching services:', error);
    }
  };

  const fetchAvailability = async (date) => {
    try {
      const dateStr = date.toISOString().split('T')[0];
      const response = await axios.get(`${API}/availability/${dateStr}`);
      setAvailableSlots(response.data.available_slots);
    } catch (error) {
      console.error('Error fetching availability:', error);
    }
  };

  const handleBooking = async () => {
    try {
      const response = await axios.post(`${API}/bookings`, bookingForm);
      alert('Booking created! Please proceed with payment.');
      setShowBookingDialog(false);
      setBookingForm({
        customer_name: '',
        customer_email: '',
        customer_phone: '',
        booking_date: '',
        booking_time: ''
      });
    } catch (error) {
      alert(error.response?.data?.detail || 'Error creating booking');
    }
  };

  const handlePaymentSubmission = async () => {
    try {
      await axios.post(`${API}/bookings/${paymentForm.booking_id}/payment`, paymentForm);
      alert('Payment submitted for admin review!');
      setShowPaymentDialog(false);
      setPaymentForm({ booking_id: '', payment_amount: '', payment_reference: '' });
    } catch (error) {
      alert(error.response?.data?.detail || 'Error submitting payment');
    }
  };

  const fetchCustomerBookings = async () => {
    try {
      const response = await axios.get(`${API}/bookings/customer/${customerEmail}`);
      setCustomerBookings(response.data);
    } catch (error) {
      console.error('Error fetching customer bookings:', error);
    }
  };

  const handleAdminLogin = async () => {
    try {
      const response = await axios.post(`${API}/admin/login`, adminForm);
      setIsAdmin(true);
      setCurrentView('admin');
      setShowAdminDialog(false); // Close the dialog
      fetchAllBookings();
      alert('Admin login successful!');
    } catch (error) {
      alert('Invalid admin credentials');
    }
  };

  const fetchAllBookings = async () => {
    try {
      const response = await axios.get(`${API}/admin/bookings`);
      setAllBookings(response.data);
    } catch (error) {
      console.error('Error fetching admin bookings:', error);
    }
  };

  const handleBookingAction = async (bookingId, action) => {
    try {
      await axios.put(`${API}/admin/bookings/${bookingId}/${action}`);
      alert(`Booking ${action}d successfully!`);
      fetchAllBookings();
    } catch (error) {
      alert(`Error ${action}ing booking`);
    }
  };

  const getServiceIcon = (type) => {
    switch (type) {
      case 'makeup': return <Palette className="w-6 h-6" />;
      case 'photography': return <Camera className="w-6 h-6" />;
      case 'video': return <Video className="w-6 h-6" />;
      case 'combo': return <Package className="w-6 h-6" />;
      default: return <Star className="w-6 h-6" />;
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'pending_payment': { color: 'bg-yellow-500', text: 'Pending Payment' },
      'payment_submitted': { color: 'bg-blue-500', text: 'Payment Review' },
      'confirmed': { color: 'bg-green-500', text: 'Confirmed' },
      'completed': { color: 'bg-gray-500', text: 'Completed' },
      'cancelled': { color: 'bg-red-500', text: 'Cancelled' }
    };
    const config = statusConfig[status] || { color: 'bg-gray-500', text: status };
    return <Badge className={`${config.color} text-white`}>{config.text}</Badge>;
  };

  const serviceImages = {
    'makeup': [
      'https://images.unsplash.com/photo-1709477542170-f11ee7d471a0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxtYWtldXAlMjBhcnRpc3R8ZW58MHx8fHwxNzU0MzQ5Mjg2fDA&ixlib=rb-4.1.0&q=85',
      'https://images.unsplash.com/photo-1636023730877-233b9237d4ec?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwzfHxtYWtldXAlMjBhcnRpc3R8ZW58MHx8fHwxNzU0MzQ5Mjg2fDA&ixlib=rb-4.1.0&q=85',
      'https://images.pexels.com/photos/1926620/pexels-photo-1926620.jpeg'
    ],
    'photography': [
      'https://images.unsplash.com/photo-1617463874381-85b513b3e991?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxwaG90b2dyYXBoeSUyMHN0dWRpb3xlbnwwfHx8fDE3NTQzNDkyOTF8MA&ixlib=rb-4.1.0&q=85',
      'https://images.unsplash.com/photo-1471341971476-ae15ff5dd4ea?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwzfHxwaG90b2dyYXBoeSUyMHN0dWRpb3xlbnwwfHx8fDE3NTQzNDkyOTF8MA&ixlib=rb-4.1.0&q=85',
      'https://images.unsplash.com/photo-1641236210747-48bc43e4517f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHw0fHxwaG90b2dyYXBoeSUyMHN0dWRpb3xlbnwwfHx8fDE3NTQzNDkyOTF8MA&ixlib=rb-4.1.0&q=85'
    ],
    'video': [
      'https://images.unsplash.com/photo-1497015289639-54688650d173?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwxfHx2aWRlbyUyMHByb2R1Y3Rpb258ZW58MHx8fHwxNzU0MzQ5Mjk2fDA&ixlib=rb-4.1.0&q=85',
      'https://images.unsplash.com/photo-1490971774356-7fac993cc438?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHw0fHx2aWRlbyUyMHByb2R1Y3Rpb258ZW58MHx8fHwxNzU0MzQ5Mjk2fDA&ixlib=rb-4.1.0&q=85',
      'https://images.pexels.com/photos/66134/pexels-photo-66134.jpeg'
    ]
  };

  if (currentView === 'admin' && isAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-black/5">
        <div className="container mx-auto px-4 py-8">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800">Admin Dashboard</h1>
            <Button onClick={() => { setCurrentView('home'); setIsAdmin(false); }} variant="outline">
              Back to Website
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>All Bookings</CardTitle>
              <CardDescription>Manage customer bookings and payments</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {allBookings.map((booking) => (
                  <div key={booking.id} className="border rounded-lg p-4 bg-white shadow-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold">{booking.customer_name}</h3>
                        <p className="text-sm text-gray-600">{booking.customer_email}</p>
                        <p className="text-sm text-gray-600">{booking.customer_phone}</p>
                        <p className="text-sm">Date: {new Date(booking.booking_date).toLocaleDateString()}</p>
                        <p className="text-sm">Time: {booking.booking_time}</p>
                        {booking.payment_amount && (
                          <p className="text-sm font-medium text-green-600">
                            Payment: ${booking.payment_amount} - Ref: {booking.payment_reference}
                          </p>
                        )}
                      </div>
                      <div className="flex flex-col gap-2 items-end">
                        {getStatusBadge(booking.status)}
                        <div className="flex gap-2">
                          {booking.status === 'payment_submitted' && (
                            <Button 
                              size="sm" 
                              onClick={() => handleBookingAction(booking.id, 'approve')}
                              className="bg-green-600 hover:bg-green-700"
                            >
                              Approve
                            </Button>
                          )}
                          {booking.status === 'confirmed' && (
                            <Button 
                              size="sm" 
                              onClick={() => handleBookingAction(booking.id, 'complete')}
                              variant="outline"
                            >
                              Mark Complete
                            </Button>
                          )}
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => handleBookingAction(booking.id, 'cancel')}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (currentView === 'customer-portal') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-black/5">
        <div className="container mx-auto px-4 py-8">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800">Customer Portal</h1>
            <Button onClick={() => setCurrentView('home')} variant="outline">
              Back to Home
            </Button>
          </div>

          <div className="max-w-md mx-auto mb-8">
            <Card>
              <CardHeader>
                <CardTitle>Access Your Bookings</CardTitle>
                <CardDescription>Enter your email to view your appointments</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="customer-email">Email Address</Label>
                  <Input
                    id="customer-email"
                    type="email"
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    placeholder="Enter your email"
                  />
                </div>
                <Button onClick={fetchCustomerBookings} className="w-full bg-pink-600 hover:bg-pink-700">
                  View My Bookings
                </Button>
              </CardContent>
            </Card>
          </div>

          {customerBookings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Your Bookings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {customerBookings.map((booking) => (
                    <div key={booking.id} className="border rounded-lg p-4 bg-white shadow-sm">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-semibold">Booking #{booking.id.slice(0, 8)}</h3>
                          <p className="text-sm text-gray-600">Date: {new Date(booking.booking_date).toLocaleDateString()}</p>
                          <p className="text-sm text-gray-600">Time: {booking.booking_time}</p>
                        </div>
                        <div className="flex flex-col gap-2 items-end">
                          {getStatusBadge(booking.status)}
                          {booking.status === 'pending_payment' && (
                            <Button
                              size="sm"
                              onClick={() => {
                                setPaymentForm(prev => ({ ...prev, booking_id: booking.id }));
                                setShowPaymentDialog(true);
                              }}
                              className="bg-pink-600 hover:bg-pink-700"
                            >
                              Submit Payment
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-black/5">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-pink-100">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-pink-600 to-black bg-clip-text text-transparent">
                Alostudio
              </h1>
            </div>
            <nav className="flex space-x-6">
              <Button variant="ghost" onClick={() => setCurrentView('home')}>Home</Button>
              <Button variant="ghost" onClick={() => setCurrentView('customer-portal')}>My Bookings</Button>
              <Dialog open={showAdminDialog} onOpenChange={setShowAdminDialog}>
                <DialogTrigger asChild>
                  <Button variant="ghost" onClick={() => setShowAdminDialog(true)}>Admin</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Admin Login</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="username">Username</Label>
                      <Input
                        id="username"
                        value={adminForm.username}
                        onChange={(e) => setAdminForm(prev => ({ ...prev, username: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label htmlFor="password">Password</Label>
                      <Input
                        id="password"
                        type="password"
                        value={adminForm.password}
                        onChange={(e) => setAdminForm(prev => ({ ...prev, password: e.target.value }))}
                      />
                    </div>
                    <Button onClick={handleAdminLogin} className="w-full bg-black hover:bg-gray-800">
                      Login
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 px-4">
        <div className="container mx-auto text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Professional Photo & Video Studio
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Transform your moments into memories with our expert makeup, photography, and video services for all occasions.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Button size="lg" className="bg-pink-600 hover:bg-pink-700 text-white px-8">
              Book Session
            </Button>
            <Button size="lg" variant="outline" className="border-pink-600 text-pink-600 hover:bg-pink-50">
              View Portfolio
            </Button>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-16 px-4">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">Our Services</h2>
          
          <Tabs defaultValue="makeup" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="makeup">Makeup</TabsTrigger>
              <TabsTrigger value="photography">Photography</TabsTrigger>
              <TabsTrigger value="video">Video</TabsTrigger>
              <TabsTrigger value="combo">Combos</TabsTrigger>
            </TabsList>
            
            <TabsContent value="makeup" className="space-y-6">
              <div className="grid md:grid-cols-3 gap-6">
                {services.filter(service => service.type === 'makeup').map((service, index) => (
                  <Card key={service.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                    <div className="aspect-video relative">
                      <img 
                        src={serviceImages.makeup[index] || serviceImages.makeup[0]} 
                        alt={service.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                          {getServiceIcon(service.type)}
                          {service.name}
                        </CardTitle>
                        <span className="text-2xl font-bold text-pink-600">${service.base_price}</span>
                      </div>
                      <CardDescription>{service.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Clock className="w-4 h-4" />
                          {service.duration_hours}h session
                        </div>
                        <Badge variant="secondary">{service.deposit_percentage}% deposit</Badge>
                      </div>
                      <Button 
                        className="w-full bg-pink-600 hover:bg-pink-700" 
                        onClick={() => {
                          setSelectedService(service);
                          setShowBookingDialog(true);
                        }}
                      >
                        Book Now
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
            
            <TabsContent value="photography" className="space-y-6">
              <div className="grid md:grid-cols-3 gap-6">
                {services.filter(service => service.type === 'photography').map((service, index) => (
                  <Card key={service.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                    <div className="aspect-video relative">
                      <img 
                        src={serviceImages.photography[index] || serviceImages.photography[0]} 
                        alt={service.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                          {getServiceIcon(service.type)}
                          {service.name}
                        </CardTitle>
                        <span className="text-2xl font-bold text-pink-600">${service.base_price}</span>
                      </div>
                      <CardDescription>{service.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <MapPin className="w-4 h-4" />
                          {service.location || 'Studio'}
                        </div>
                        <Badge variant="secondary">{service.deposit_percentage}% deposit</Badge>
                      </div>
                      <Button 
                        className="w-full bg-pink-600 hover:bg-pink-700" 
                        onClick={() => {
                          setSelectedService(service);
                          setShowBookingDialog(true);
                        }}
                      >
                        Book Session
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
            
            <TabsContent value="video" className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                {services.filter(service => service.type === 'video').map((service, index) => (
                  <Card key={service.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                    <div className="aspect-video relative">
                      <img 
                        src={serviceImages.video[index] || serviceImages.video[0]} 
                        alt={service.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                          {getServiceIcon(service.type)}
                          {service.name}
                        </CardTitle>
                        <span className="text-2xl font-bold text-pink-600">${service.base_price}</span>
                      </div>
                      <CardDescription>{service.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <MapPin className="w-4 h-4" />
                          {service.location || 'Studio'}
                        </div>
                        <Badge variant="secondary">{service.deposit_percentage}% deposit</Badge>
                      </div>
                      <Button 
                        className="w-full bg-pink-600 hover:bg-pink-700" 
                        onClick={() => {
                          setSelectedService(service);
                          setShowBookingDialog(true);
                        }}
                      >
                        Book Session
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
            
            <TabsContent value="combo">
              <div className="text-center py-12">
                <Package className="w-16 h-16 mx-auto text-pink-600 mb-4" />
                <h3 className="text-2xl font-bold mb-4">Alo Combos Coming Soon!</h3>
                <p className="text-gray-600 mb-6">
                  Get discounted rates when you combine makeup with photography or video sessions.
                </p>
                <Button variant="outline" className="border-pink-600 text-pink-600">
                  Notify Me
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold text-pink-400 mb-4">Alostudio</h3>
              <p className="text-gray-300">Professional photo and video studio for all your special moments.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Services</h4>
              <ul className="space-y-2 text-gray-300">
                <li>Makeup Services</li>
                <li>Photography</li>
                <li>Video Production</li>
                <li>Event Coverage</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Contact</h4>
              <ul className="space-y-2 text-gray-300">
                <li>CashApp: $VitiPay</li>
                <li>Email: info@alostudio.com</li>
                <li>Phone: (555) 123-4567</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Policies</h4>
              <ul className="space-y-2 text-gray-300">
                <li>No Refund Policy</li>
                <li>Processing: 1-2 weeks</li>
                <li>Late Fee Applies</li>
              </ul>
            </div>
          </div>
        </div>
      </footer>

      {/* Booking Dialog */}
      <Dialog open={showBookingDialog} onOpenChange={setShowBookingDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Book {selectedService?.name}</DialogTitle>
            <DialogDescription>
              ${selectedService?.base_price} - {selectedService?.deposit_percentage}% deposit required
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                value={bookingForm.customer_name}
                onChange={(e) => setBookingForm(prev => ({ ...prev, customer_name: e.target.value }))}
                placeholder="Enter your name"
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={bookingForm.customer_email}
                onChange={(e) => setBookingForm(prev => ({ ...prev, customer_email: e.target.value }))}
                placeholder="Enter your email"
              />
            </div>
            <div>
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                value={bookingForm.customer_phone}
                onChange={(e) => setBookingForm(prev => ({ ...prev, customer_phone: e.target.value }))}
                placeholder="Enter your phone number"
              />
            </div>
            <div>
              <Label htmlFor="date">Date</Label>
              <Input
                id="date"
                type="date"
                value={bookingForm.booking_date}
                onChange={(e) => {
                  setBookingForm(prev => ({ ...prev, booking_date: e.target.value }));
                  if (e.target.value) {
                    fetchAvailability(new Date(e.target.value));
                  }
                }}
              />
            </div>
            {availableSlots.length > 0 && (
              <div>
                <Label>Available Times</Label>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  {availableSlots.map((slot) => (
                    <Button
                      key={slot}
                      variant={bookingForm.booking_time === slot ? "default" : "outline"}
                      size="sm"
                      onClick={() => setBookingForm(prev => ({ ...prev, booking_time: slot }))}
                      className={bookingForm.booking_time === slot ? "bg-pink-600 hover:bg-pink-700" : ""}
                    >
                      {slot}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            <Button 
              onClick={handleBooking} 
              className="w-full bg-pink-600 hover:bg-pink-700"
              disabled={!bookingForm.customer_name || !bookingForm.customer_email || !bookingForm.booking_date || !bookingForm.booking_time}
            >
              Create Booking
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit Payment</DialogTitle>
            <DialogDescription>
              Send payment via CashApp to $VitiPay and enter details below
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 bg-pink-50 rounded-lg">
              <p className="font-semibold text-pink-800">Payment Instructions:</p>
              <p className="text-pink-700">Send payment to CashApp: <strong>$VitiPay</strong></p>
            </div>
            <div>
              <Label htmlFor="amount">Amount Paid</Label>
              <Input
                id="amount"
                type="number"
                value={paymentForm.payment_amount}
                onChange={(e) => setPaymentForm(prev => ({ ...prev, payment_amount: e.target.value }))}
                placeholder="Enter amount"
              />
            </div>
            <div>
              <Label htmlFor="reference">Payment Reference/ID</Label>
              <Input
                id="reference"
                value={paymentForm.payment_reference}
                onChange={(e) => setPaymentForm(prev => ({ ...prev, payment_reference: e.target.value }))}
                placeholder="Enter transaction ID or reference"
              />
            </div>
            <Button 
              onClick={handlePaymentSubmission} 
              className="w-full bg-pink-600 hover:bg-pink-700"
            >
              Submit Payment Info
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;