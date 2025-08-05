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
import { Checkbox } from './components/ui/checkbox';
import { Clock, Calendar as CalendarIcon, MapPin, Star, Camera, Video, Palette, Package, Edit3, Image, Users, CheckCircle, Clock as ClockIcon, AlertCircle, MessageCircle, Phone, Heart, Gift, Cloud } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [services, setServices] = useState([]);
  const [comboServices, setComboServices] = useState([]);
  const [settings, setSettings] = useState({});
  const [selectedService, setSelectedService] = useState(null);
  const [bookingForm, setBookingForm] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    booking_date: '',
    booking_time: '',
    service_id: '',
    has_paid: false
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
  const [adminSettings, setAdminSettings] = useState({ whatsapp_number: '', cashapp_id: '' });
  const [adminToken, setAdminToken] = useState(localStorage.getItem('admin_token') || '');
  const [earnings, setEarnings] = useState({});
  const [frameOrders, setFrameOrders] = useState([]);
  
  // User dashboard state
  const [userPhotos, setUserPhotos] = useState([]);
  const [userDashboard, setUserDashboard] = useState(null);
  const [selectedPhotos, setSelectedPhotos] = useState([]);
  const [frameOrderForm, setFrameOrderForm] = useState({
    frame_size: '8x10',
    frame_style: 'modern',
    quantity: 1,
    special_instructions: ''
  });

  // Check if current URL contains manage hash for admin access
  const [showAdminAccess, setShowAdminAccess] = useState(false);
  
  useEffect(() => {
    // Check for admin access via URL hash or query parameter
    const checkAdminAccess = () => {
      const url = window.location.href.toLowerCase();
      const hasManage = url.includes('/manage') || url.includes('#manage') || url.includes('?admin') || url.includes('manage');
      setShowAdminAccess(hasManage);
    };
    
    checkAdminAccess();
    // Listen for URL changes
    window.addEventListener('popstate', checkAdminAccess);
    
    return () => {
      window.removeEventListener('popstate', checkAdminAccess);
    };
  }, []);

  // Scroll functions
  const scrollToServices = () => {
    const servicesSection = document.querySelector('#services-section');
    if (servicesSection) {
      servicesSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToPortfolio = () => {
    // For now, scroll to services section - you can create a portfolio section later
    scrollToServices();
  };

  const scrollToServiceType = (serviceType) => {
    // First scroll to services section
    scrollToServices();
    // Wait a moment then switch tab
    setTimeout(() => {
      const tabButton = document.querySelector(`[value="${serviceType}"]`);
      if (tabButton) {
        tabButton.click();
      }
    }, 500);
  };

  useEffect(() => {
    fetchServices();
    fetchComboServices();
    fetchSettings();
  }, []);

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API}/services`);
      setServices(response.data);
    } catch (error) {
      console.error('Error fetching services:', error);
    }
  };

  const fetchComboServices = async () => {
    try {
      const response = await axios.get(`${API}/combo-services`);
      setComboServices(response.data);
    } catch (error) {
      console.error('Error fetching combo services:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Error fetching settings:', error);
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
      // Ensure service_id is set
      const bookingData = {
        ...bookingForm,
        service_id: selectedService?.id || bookingForm.service_id
      };
      
      console.log('Booking data:', bookingData); // Debug log
      const response = await axios.post(`${API}/bookings`, bookingData);
      
      // If user has paid, automatically submit payment info
      if (bookingForm.has_paid) {
        const depositAmount = ((selectedService?.base_price || 0) * (selectedService?.deposit_percentage || 0) / 100).toFixed(2);
        const paymentData = {
          booking_id: response.data.id,
          payment_amount: parseFloat(depositAmount),
          payment_reference: `User confirmed payment via booking form - ${new Date().toISOString().slice(0, 10)}`
        };
        
        await axios.post(`${API}/bookings/${response.data.id}/payment`, paymentData);
        alert('Booking created and payment info submitted! Admin will review and approve your payment.');
      } else {
        alert('Booking created! Please proceed with payment.');
      }
      
      setShowBookingDialog(false);
      setBookingForm({
        customer_name: '',
        customer_email: '',
        customer_phone: '',
        booking_date: '',
        booking_time: '',
        service_id: '',
        has_paid: false
      });
    } catch (error) {
      console.error('Booking error:', error.response?.data);
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
      setShowAdminDialog(false);
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

  const handleUpdateSettings = async () => {
    try {
      await axios.put(`${API}/admin/settings`, adminSettings);
      alert('Settings updated successfully!');
      fetchSettings();
    } catch (error) {
      alert('Error updating settings');
    }
  };

  const getServiceIcon = (type) => {
    switch (type) {
      case 'makeup': return <Palette className="w-6 h-6" />;
      case 'photography': return <Camera className="w-6 h-6" />;
      case 'video': return <Video className="w-6 h-6" />;
      case 'combo': return <Package className="w-6 h-6" />;
      case 'editing': return <Edit3 className="w-6 h-6" />;
      case 'graphic_design': return <Image className="w-6 h-6" />;
      case 'memory_storage': return <Cloud className="w-6 h-6" />;
      case 'frames': return <Gift className="w-6 h-6" />;
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
      'https://images.unsplash.com/photo-1641236210747-48bc43e4517f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHw0fHxwaG90b2dyYXBoeSUyMHN0dWRpb3xlbnwwfHx8fDE3NTQzNDkyOTF8MA&ixlib=rb-4.1.0&q=85',
      'https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwyfHxwaG90byUyMHN0dWRpbyUyMGludGVyaW9yfGVufDB8fHx8MTc1NDM0OTYyMXww&ixlib=rb-4.1.0&q=85'
    ],
    'video': [
      'https://images.unsplash.com/photo-1497015289639-54688650d173?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwxfHx2aWRlbyUyMHByb2R1Y3Rpb258ZW58MHx8fHwxNzU0MzQ5Mjk2fDA&ixlib=rb-4.1.0&q=85',
      'https://images.unsplash.com/photo-1490971774356-7fac993cc438?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHw0fHx2aWRlbyUyMHByb2R1Y3Rpb258ZW58MHx8fHwxNzU0MzQ5Mjk2fDA&ixlib=rb-4.1.0&q=85'
    ],
    'editing': [
      'https://images.unsplash.com/photo-1574717024239-25253f4ef40a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwyfHx2aWRlbyUyMGVkaXRpbmclMjB3b3Jrc3BhY2V8ZW58MHx8fHwxNzU0MzQ5NjU5fDA&ixlib=rb-4.1.0&q=85',
      'https://images.unsplash.com/photo-1574717025058-2f8737d2e2b7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwzfHx2aWRlbyUyMGVkaXRpbmclMjB3b3Jrc3BhY2V8ZW58MHx8fHwxNzU0MzQ5NjU5fDA&ixlib=rb-4.1.0&q=85'
    ],
    'memory_storage': 'https://images.unsplash.com/photo-1506399558188-acca6f8cbf41?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwxfHxkaWdpdGFsJTIwc3RvcmFnZSUyMGNsb3VkfGVufDB8fHx8MTc1NDM0OTY5MXww&ixlib=rb-4.1.0&q=85',
    'frames': 'https://images.unsplash.com/photo-1554907984-15263bfd63bd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwyfHxwaWN0dXJlJTIwZnJhbWVzJTIwZGlzcGxheXxlbnwwfHx8fDE3NTQzNDk3MTN8MA&ixlib=rb-4.1.0&q=85',
    'combo': 'https://images.unsplash.com/photo-1647427854253-b92bb40c9330?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwyfHxwaG90byUyMHN0dWRpbyUyMGludGVyaW9yfGVufDB8fHx8MTc1NDM0OTYyMXww&ixlib=rb-4.1.0&q=85'
  };

  // WhatsApp Chat Component
  const WhatsAppChat = () => (
    <div className="fixed bottom-20 right-6 z-50">
      <Button
        className="bg-green-500 hover:bg-green-600 rounded-full p-4 shadow-lg bounce-in"
        onClick={() => {
          const phone = settings.whatsapp_number?.replace('+', '');
          const message = encodeURIComponent("Hi! I'm interested in Alostudio services.");
          const whatsappURL = `https://wa.me/${phone}?text=${message}`;
          window.open(whatsappURL, '_blank');
        }}
      >
        <MessageCircle className="w-6 h-6" />
      </Button>
    </div>
  );

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

          <div className="grid lg:grid-cols-2 gap-8">
            <Card>
              <CardHeader>
                <CardTitle>All Bookings</CardTitle>
                <CardDescription>Manage customer bookings and payments</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {allBookings.map((booking) => (
                    <div key={booking.id} className="border rounded-lg p-4 bg-white shadow-sm">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-semibold">{booking.customer_name}</h3>
                          <p className="text-sm text-gray-600">{booking.customer_email}</p>
                          <p className="text-sm text-gray-600">{booking.customer_phone}</p>
                          <p className="text-sm">Service: {booking.service_type}</p>
                          <p className="text-sm">Date: {new Date(booking.booking_date).toLocaleDateString()}</p>
                          <p className="text-sm">Time: {booking.booking_time}</p>
                          {booking.payment_amount && (
                            <p className="text-sm font-medium text-green-600">
                              Payment: ${booking.payment_amount} - Ref: {booking.payment_reference}
                            </p>
                          )}
                        </div>
                        <div className="flex flex-col gap-2 items-end mobile-admin-actions">
                          {getStatusBadge(booking.status)}
                          <div className="flex flex-col md:flex-row gap-2 w-full md:w-auto">
                            {booking.status === 'payment_submitted' && (
                              <Button 
                                size="sm" 
                                onClick={() => handleBookingAction(booking.id, 'approve')}
                                className="bg-green-600 hover:bg-green-700 w-full md:w-auto"
                              >
                                Approve Payment
                              </Button>
                            )}
                            {booking.status === 'confirmed' && (
                              <Button 
                                size="sm" 
                                onClick={() => handleBookingAction(booking.id, 'complete')}
                                variant="outline"
                                className="w-full md:w-auto"
                              >
                                Mark Complete
                              </Button>
                            )}
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleBookingAction(booking.id, 'cancel')}
                              className="w-full md:w-auto"
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

            <Card>
              <CardHeader>
                <CardTitle>Settings</CardTitle>
                <CardDescription>Update business settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="whatsapp">WhatsApp Number</Label>
                  <Input
                    id="whatsapp"
                    value={adminSettings.whatsapp_number || settings.whatsapp_number}
                    onChange={(e) => setAdminSettings(prev => ({ ...prev, whatsapp_number: e.target.value }))}
                    placeholder="+16144055997"
                  />
                </div>
                <div>
                  <Label htmlFor="cashapp">CashApp ID</Label>
                  <Input
                    id="cashapp"
                    value={adminSettings.cashapp_id || settings.cashapp_id}
                    onChange={(e) => setAdminSettings(prev => ({ ...prev, cashapp_id: e.target.value }))}
                    placeholder="$VitiPay"
                  />
                </div>
                <Button onClick={handleUpdateSettings} className="w-full bg-pink-600 hover:bg-pink-700">
                  Update Settings
                </Button>
              </CardContent>
            </Card>
          </div>
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
                          <p className="text-sm text-gray-600">Service: {booking.service_type}</p>
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
        <WhatsAppChat />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-black/5">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-pink-100 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4 mobile-header">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 md:gap-0">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-pink-600 to-black bg-clip-text text-transparent">
                Alostudio
              </h1>
            </div>
            <nav className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-6 w-full md:w-auto mobile-nav">
              <Button variant="ghost" onClick={() => setCurrentView('home')} className="w-full md:w-auto">Home</Button>
              <Button variant="ghost" onClick={() => setCurrentView('customer-portal')} className="w-full md:w-auto">My Bookings</Button>
              {showAdminAccess && (
                <Dialog open={showAdminDialog} onOpenChange={setShowAdminDialog}>
                  <DialogTrigger asChild>
                    <Button variant="ghost" onClick={() => setShowAdminDialog(true)} className="w-full md:w-auto">Admin</Button>
                  </DialogTrigger>
                  <DialogContent className="mobile-dialog">
                    <DialogHeader>
                      <DialogTitle>Admin Login</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mobile-form">
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
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-12 md:py-20 px-4 bg-gradient-to-r from-pink-100 via-white to-pink-50 mobile-hero">
        <div className="absolute inset-0 opacity-10 bg-cover bg-center" 
             style={{backgroundImage: 'url(https://images.unsplash.com/photo-1647427854253-b92bb40c9330?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwyfHxwaG90byUyMHN0dWRpbyUyMGludGVyaW9yfGVufDB8fHx8MTc1NDM0OTYyMXww&ixlib=rb-4.1.0&q=85)'}}></div>
        <div className="container mx-auto text-center relative z-10">
          <h2 className="text-3xl md:text-6xl font-bold text-gray-900 mb-4 md:mb-6 fade-in-up leading-tight">
            Professional Photo & Video Studio
          </h2>
          <p className="text-base md:text-xl text-gray-600 mb-6 md:mb-8 max-w-2xl mx-auto px-4">
            Transform your moments into memories with our expert makeup, photography, and video services for all occasions including weddings, birthdays, events, and more.
          </p>
          <div className="flex flex-col md:flex-row justify-center gap-4 mobile-hero-buttons px-4">
            <Button size="lg" onClick={scrollToServices} className="bg-pink-600 hover:bg-pink-700 text-white px-6 md:px-8 shadow-lg hover-lift w-full md:w-auto">
              Book Session
            </Button>
            <Button size="lg" onClick={scrollToPortfolio} variant="outline" className="border-pink-600 text-pink-600 hover:bg-pink-50 shadow-lg hover-lift w-full md:w-auto">
              View Portfolio
            </Button>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section id="services-section" className="py-12 md:py-16 px-4 mobile-services">
        <div className="container mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-8 md:mb-12 text-gray-900">Our Services</h2>
          
          <Tabs defaultValue="makeup" className="w-full mobile-tabs">
            <div className="overflow-x-auto scrollbar-hide">
              <TabsList className="grid grid-cols-6 min-w-max md:w-full mb-6 md:mb-8 text-xs md:text-sm">
                <TabsTrigger value="makeup" className="px-3 md:px-4 whitespace-nowrap">Makeup</TabsTrigger>
                <TabsTrigger value="photography" className="px-3 md:px-4 whitespace-nowrap">Photo</TabsTrigger>
                <TabsTrigger value="video" className="px-3 md:px-4 whitespace-nowrap">Video</TabsTrigger>
                <TabsTrigger value="combo" className="px-3 md:px-4 whitespace-nowrap">Combos</TabsTrigger>
                <TabsTrigger value="editing" className="px-3 md:px-4 whitespace-nowrap">Editing</TabsTrigger>
                <TabsTrigger value="extras" className="px-3 md:px-4 whitespace-nowrap">Extras</TabsTrigger>
              </TabsList>
            </div>
            
            <TabsContent value="makeup" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                {services.filter(service => service.type === 'makeup').map((service, index) => (
                  <Card key={service.id} className="overflow-hidden hover:shadow-xl transition-all duration-300 service-card hover-lift mobile-service-card">
                    <div className="aspect-video relative image-overlay">
                      <img 
                        src={serviceImages.makeup[index] || serviceImages.makeup[0]} 
                        alt={service.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <CardHeader className="p-4 md:p-6">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 md:gap-0">
                        <CardTitle className="flex items-center gap-2 text-lg md:text-xl">
                          {getServiceIcon(service.type)}
                          {service.name}
                        </CardTitle>
                        <span className="text-xl md:text-2xl font-bold text-pink-600">${service.base_price}</span>
                      </div>
                      <CardDescription className="text-sm md:text-base">{service.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="p-4 md:p-6 pt-0">
                      <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 gap-2 md:gap-0">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Clock className="w-4 h-4" />
                          {service.duration_hours}h session
                        </div>
                        <Badge variant="secondary" className="bg-pink-100 text-pink-800 w-fit">{service.deposit_percentage}% deposit</Badge>
                      </div>
                      {service.features && (
                        <div className="mb-4">
                          <p className="text-sm font-medium text-gray-700 mb-2">Includes:</p>
                          <ul className="text-xs text-gray-600 space-y-1">
                            {service.features.slice(0, 3).map((feature, idx) => (
                              <li key={idx} className="flex items-center gap-1">
                                <CheckCircle className="w-3 h-3 text-green-500 flex-shrink-0" />
                                <span className="text-xs">{feature}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <Button 
                        className="w-full bg-pink-600 hover:bg-pink-700 shadow-lg" 
                        onClick={() => {
                          setSelectedService(service);
                          setBookingForm(prev => ({ ...prev, service_id: service.id }));
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
                {services.filter(service => service.type === 'photography').map((service, index) => (
                  <Card key={service.id} className="overflow-hidden hover:shadow-xl transition-all duration-300 service-card hover-lift mobile-service-card">
                    <div className="aspect-video relative image-overlay">
                      <img 
                        src={serviceImages.photography[index] || serviceImages.photography[0]} 
                        alt={service.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <CardHeader className="p-4 md:p-6">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 md:gap-0">
                        <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                          {getServiceIcon(service.type)}
                          <span className="text-sm md:text-base">{service.name}</span>
                        </CardTitle>
                        <span className="text-lg md:text-xl font-bold text-pink-600">${service.base_price}</span>
                      </div>
                      <CardDescription className="text-xs md:text-sm">{service.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="p-4 md:p-6 pt-0">
                      <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 gap-2 md:gap-0">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <MapPin className="w-4 h-4" />
                          {service.location || 'Studio'}
                        </div>
                        <Badge variant="secondary" className="bg-pink-100 text-pink-800 w-fit">{service.deposit_percentage}% deposit</Badge>
                      </div>
                      {service.features && (
                        <div className="mb-4">
                          <ul className="text-xs text-gray-600 space-y-1">
                            {service.features.slice(0, 3).map((feature, idx) => (
                              <li key={idx} className="flex items-center gap-1">
                                <CheckCircle className="w-3 h-3 text-green-500 flex-shrink-0" />
                                <span className="text-xs">{feature}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <Button 
                        className="w-full bg-pink-600 hover:bg-pink-700 shadow-lg" 
                        onClick={() => {
                          setSelectedService(service);
                          setBookingForm(prev => ({ ...prev, service_id: service.id }));
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
                  <Card key={service.id} className="overflow-hidden hover:shadow-xl transition-all duration-300 service-card hover-lift">
                    <div className="aspect-video relative image-overlay">
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
                        <Badge variant="secondary" className="bg-pink-100 text-pink-800">{service.deposit_percentage}% deposit</Badge>
                      </div>
                      {service.features && (
                        <div className="mb-4">
                          <ul className="text-xs text-gray-600 space-y-1">
                            {service.features.slice(0, 4).map((feature, idx) => (
                              <li key={idx} className="flex items-center gap-1">
                                <CheckCircle className="w-3 h-3 text-green-500" />
                                {feature}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <Button 
                        className="w-full bg-pink-600 hover:bg-pink-700 shadow-lg" 
                        onClick={() => {
                          setSelectedService(service);
                          setBookingForm(prev => ({ ...prev, service_id: service.id }));
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
              <div className="grid md:grid-cols-3 gap-6">
                {comboServices.map((combo) => (
                  <Card key={combo.id} className="overflow-hidden hover:shadow-xl transition-all duration-300 service-card hover-lift border-2 border-pink-200">
                    <div className="aspect-video relative image-overlay">
                      <img 
                        src={serviceImages.combo} 
                        alt={combo.name}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute top-4 right-4">
                        <Badge className="bg-green-500 text-white">15% OFF</Badge>
                      </div>
                    </div>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                          <Package className="w-6 h-6" />
                          {combo.name}
                        </CardTitle>
                        <div className="text-right">
                          <p className="text-lg line-through text-gray-400">${combo.total_price}</p>
                          <p className="text-2xl font-bold text-pink-600">${combo.final_price}</p>
                        </div>
                      </div>
                      <CardDescription>{combo.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Clock className="w-4 h-4" />
                          {combo.duration_hours}h total
                        </div>
                        <Badge variant="secondary" className="bg-green-100 text-green-800">Save ${(combo.total_price - combo.final_price).toFixed(2)}</Badge>
                      </div>
                      <Button 
                        className="w-full bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 shadow-lg" 
                        onClick={() => {
                          setSelectedService({...combo, type: 'combo', deposit_percentage: 25, base_price: combo.final_price});
                          setBookingForm(prev => ({ ...prev, service_id: combo.id }));
                          setShowBookingDialog(true);
                        }}
                      >
                        Book Combo
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
            
            <TabsContent value="editing">
              <div className="grid md:grid-cols-3 gap-6">
                {services.filter(service => service.type === 'editing' || service.type === 'graphic_design').map((service, index) => (
                  <Card key={service.id} className="overflow-hidden hover:shadow-xl transition-all duration-300 service-card hover-lift">
                    <div className="aspect-video relative image-overlay">
                      <img 
                        src={serviceImages.editing[index] || serviceImages.editing[0]} 
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
                          {service.duration_hours > 0 ? `${service.duration_hours}h` : 'Quick turnaround'}
                        </div>
                        <Badge variant="secondary" className="bg-blue-100 text-blue-800">{service.deposit_percentage}% deposit</Badge>
                      </div>
                      {service.features && (
                        <div className="mb-4">
                          <ul className="text-xs text-gray-600 space-y-1">
                            {service.features.slice(0, 3).map((feature, idx) => (
                              <li key={idx} className="flex items-center gap-1">
                                <CheckCircle className="w-3 h-3 text-green-500" />
                                {feature}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <Button 
                        className="w-full bg-pink-600 hover:bg-pink-700 shadow-lg" 
                        onClick={() => {
                          setSelectedService(service);
                          setBookingForm(prev => ({ ...prev, service_id: service.id }));
                          setShowBookingDialog(true);
                        }}
                      >
                        Order Now
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="extras">
              <div className="grid md:grid-cols-2 gap-6">
                {services.filter(service => service.type === 'memory_storage' || service.type === 'frames').map((service) => (
                  <Card key={service.id} className="overflow-hidden hover:shadow-xl transition-all duration-300 service-card hover-lift">
                    <div className="aspect-video relative image-overlay">
                      <img 
                        src={service.type === 'memory_storage' ? serviceImages.memory_storage : serviceImages.frames} 
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
                      {service.features && (
                        <div className="mb-4">
                          <ul className="text-xs text-gray-600 space-y-1">
                            {service.features.map((feature, idx) => (
                              <li key={idx} className="flex items-center gap-1">
                                <CheckCircle className="w-3 h-3 text-green-500" />
                                {feature}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <Button 
                        className="w-full bg-pink-600 hover:bg-pink-700 shadow-lg" 
                        onClick={() => {
                          setSelectedService(service);
                          setBookingForm(prev => ({ ...prev, service_id: service.id }));
                          setShowBookingDialog(true);
                        }}
                      >
                        {service.type === 'memory_storage' ? 'Get Storage' : 'Order Frames'}
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </section>

      {/* Why Choose Us Section */}
      <section className="py-12 md:py-16 px-4 bg-gradient-to-r from-pink-50 to-white mobile-why-choose">
        <div className="container mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-8 md:mb-12 text-gray-900">Why Choose Alostudio</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-pink-600" />
              </div>
              <h3 className="text-lg md:text-xl font-semibold mb-2">Expert Team</h3>
              <p className="text-gray-600 text-sm md:text-base">Professional makeup artists, photographers, and videographers with years of experience.</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Camera className="w-8 h-8 text-pink-600" />
              </div>
              <h3 className="text-lg md:text-xl font-semibold mb-2">Latest Equipment</h3>
              <p className="text-gray-600 text-sm md:text-base">State-of-the-art cameras, lighting, and professional studio equipment for perfect results.</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Heart className="w-8 h-8 text-pink-600" />
              </div>
              <h3 className="text-lg md:text-xl font-semibold mb-2">All Occasions</h3>
              <p className="text-gray-600 text-sm md:text-base">Weddings, birthdays, events, baby showers, community gatherings - we cover it all.</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-pink-600" />
              </div>
              <h3 className="text-lg md:text-xl font-semibold mb-2">Quality Guaranteed</h3>
              <p className="text-gray-600 text-sm md:text-base">Professional editing with 1-2 week processing time and satisfaction guarantee.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black text-white py-8 md:py-12 mobile-footer">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 md:gap-8">
            <div className="text-center md:text-left">
              <h3 className="text-xl font-bold text-pink-400 mb-4">Alostudio</h3>
              <p className="text-gray-300 text-sm md:text-base">Professional photo and video studio for all your special moments and occasions.</p>
            </div>
            <div className="text-center md:text-left">
              <h4 className="font-semibold mb-4">Services</h4>
              <ul className="space-y-2 text-gray-300 text-sm md:text-base">
                <li><button onClick={() => scrollToServiceType('makeup')} className="hover:text-pink-400 transition-colors">Makeup Services</button></li>
                <li><button onClick={() => scrollToServiceType('photography')} className="hover:text-pink-400 transition-colors">Photography Sessions</button></li>
                <li><button onClick={() => scrollToServiceType('video')} className="hover:text-pink-400 transition-colors">Video Production</button></li>
                <li><button onClick={() => scrollToServiceType('editing')} className="hover:text-pink-400 transition-colors">Professional Editing</button></li>
              </ul>
            </div>
            <div className="text-center md:text-left">
              <h4 className="font-semibold mb-4">Contact</h4>
              <ul className="space-y-2 text-gray-300 text-sm md:text-base">
                <li>WhatsApp: {settings.whatsapp_number}</li>
                <li>Email: info@alostudio.com</li>
                <li>Phone: (555) 123-4567</li>
              </ul>
            </div>
            <div className="text-center md:text-left">
              <h4 className="font-semibold mb-4">Policies</h4>
              <ul className="space-y-2 text-gray-300 text-sm md:text-base">
                <li>No Refund Policy (User Cancellation)</li>
                <li>Processing: 1-2 weeks</li>
                <li>Late Fee for Indoor Sessions</li>
                <li>Admin Cancellation: Refund Available</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-700 mt-6 md:mt-8 pt-6 md:pt-8 text-center text-gray-400">
            <p className="text-sm md:text-base">&copy; 2025 Alostudio. All rights reserved. | Professional Photo & Video Studio</p>
          </div>
        </div>
      </footer>

      {/* WhatsApp Chat Button - Mobile Responsive */}
      <div className="fixed bottom-16 md:bottom-20 right-4 md:right-6 z-50 mobile-whatsapp">
        <Button
          className="bg-green-500 hover:bg-green-600 rounded-full p-3 md:p-4 shadow-xl bounce-in"
          onClick={() => {
            const phone = settings.whatsapp_number?.replace('+', '');
            const message = encodeURIComponent("Hi! I'm interested in Alostudio services.");
            const whatsappURL = `https://wa.me/${phone}?text=${message}`;
            window.open(whatsappURL, '_blank');
          }}
        >
          <MessageCircle className="w-5 h-5 md:w-6 md:h-6" />
        </Button>
      </div>

      {/* Booking Dialog */}
      <Dialog open={showBookingDialog} onOpenChange={setShowBookingDialog}>
        <DialogContent className="max-w-md mx-4 mobile-dialog">
          <DialogHeader>
            <DialogTitle className="text-lg md:text-xl">Book {selectedService?.name}</DialogTitle>
            <DialogDescription className="text-sm md:text-base">
              ${selectedService?.base_price} - {selectedService?.deposit_percentage}% deposit required
              {selectedService?.type === 'combo' && (
                <span className="block text-green-600 font-medium mt-1">
                  🎉 15% Discount Applied!
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mobile-form">
            <div>
              <Label htmlFor="name" className="text-sm">Full Name</Label>
              <Input
                id="name"
                value={bookingForm.customer_name}
                onChange={(e) => setBookingForm(prev => ({ ...prev, customer_name: e.target.value }))}
                placeholder="Enter your name"
                className="text-base"
              />
            </div>
            <div>
              <Label htmlFor="email" className="text-sm">Email</Label>
              <Input
                id="email"
                type="email"
                value={bookingForm.customer_email}
                onChange={(e) => setBookingForm(prev => ({ ...prev, customer_email: e.target.value }))}
                placeholder="Enter your email"
                className="text-base"
              />
            </div>
            <div>
              <Label htmlFor="phone" className="text-sm">Phone</Label>
              <Input
                id="phone"
                value={bookingForm.customer_phone}
                onChange={(e) => setBookingForm(prev => ({ ...prev, customer_phone: e.target.value }))}
                placeholder="Enter your phone number"
                className="text-base"
              />
            </div>
            <div>
              <Label htmlFor="date" className="text-sm">Date</Label>
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
                className="text-base"
              />
            </div>
            {availableSlots.length > 0 && (
              <div>
                <Label className="text-sm">Available Times</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2 max-h-32 overflow-y-auto mobile-time-slots">
                  {availableSlots.map((slot) => (
                    <Button
                      key={slot}
                      variant={bookingForm.booking_time === slot ? "default" : "outline"}
                      size="sm"
                      onClick={() => setBookingForm(prev => ({ ...prev, booking_time: slot }))}
                      className={`text-xs md:text-sm ${bookingForm.booking_time === slot ? "bg-pink-600 hover:bg-pink-700" : ""}`}
                    >
                      {slot}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            <div className="bg-pink-50 p-3 md:p-4 rounded-lg border-l-4 border-pink-500">
              <p className="text-sm text-pink-800 font-medium mb-3">
                <strong>Payment Instructions:</strong>
              </p>
              <p className="text-sm text-pink-700 mb-3">
                Send {selectedService?.deposit_percentage}% deposit 
                (${((selectedService?.base_price || 0) * (selectedService?.deposit_percentage || 0) / 100).toFixed(2)}) 
                to CashApp: <strong>{settings.cashapp_id}</strong>
              </p>
              <div className="flex items-start space-x-3 mb-3">
                <input
                  type="checkbox"
                  id="has_paid"
                  checked={bookingForm.has_paid}
                  onChange={(e) => setBookingForm(prev => ({ ...prev, has_paid: e.target.checked }))}
                  className="mt-1 h-4 w-4 text-pink-600 border-gray-300 rounded focus:ring-pink-500"
                />
                <Label htmlFor="has_paid" className="text-sm font-medium text-pink-800 leading-tight">
                  I have sent the payment to the CashApp above
                </Label>
              </div>
              <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                <p className="text-xs text-yellow-800 font-semibold">
                  ⚠️ Important: Only paid appointments are considered booked. Please ensure payment is sent before confirming your booking.
                </p>
              </div>
            </div>
            <Button 
              onClick={handleBooking} 
              className="w-full bg-pink-600 hover:bg-pink-700 py-3"
              disabled={!bookingForm.customer_name || !bookingForm.customer_email || !bookingForm.booking_date || !bookingForm.booking_time || !bookingForm.service_id || !bookingForm.has_paid}
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
              Send payment via CashApp and enter details below
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 bg-pink-50 rounded-lg">
              <p className="font-semibold text-pink-800">Payment Instructions:</p>
              <p className="text-pink-700">Send payment to CashApp: <strong>{settings.cashapp_id}</strong></p>
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