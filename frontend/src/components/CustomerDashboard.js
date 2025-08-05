import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { CheckCircle, Camera, Package, Clock, Image as ImageIcon, ShoppingCart } from 'lucide-react';

export const CustomerDashboard = ({ 
  userDashboard, 
  selectedPhotos, 
  setSelectedPhotos, 
  frameOrderForm, 
  setFrameOrderForm, 
  handleFrameOrder, 
  handleFramePayment,
  settings,
  onBookSession,
  onImageZoom
}) => {
  const [showFrameDialog, setShowFrameDialog] = useState(false);
  
  const togglePhotoSelection = (photoId) => {
    setSelectedPhotos(prev => 
      prev.includes(photoId) 
        ? prev.filter(id => id !== photoId)
        : [...prev, photoId]
    );
  };

  const getFramePrice = (size) => {
    const prices = {
      "5x7": 25.0,
      "8x10": 45.0,
      "11x14": 75.0,
      "16x20": 120.0
    };
    return prices[size] || 45.0;
  };

  const calculateFrameTotal = () => {
    const basePrice = getFramePrice(frameOrderForm.frame_size);
    return basePrice * frameOrderForm.quantity * selectedPhotos.length;
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

  if (!userDashboard) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-gray-500">Loading your dashboard...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <ImageIcon className="w-8 h-8 mx-auto mb-2 text-pink-600" />
            <div className="text-2xl font-bold text-gray-900">{userDashboard.stats.total_photos}</div>
            <p className="text-sm text-gray-600">Photos</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Camera className="w-8 h-8 mx-auto mb-2 text-pink-600" />
            <div className="text-2xl font-bold text-gray-900">{userDashboard.stats.total_bookings}</div>
            <p className="text-sm text-gray-600">Bookings</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Clock className="w-8 h-8 mx-auto mb-2 text-pink-600" />
            <div className="text-2xl font-bold text-gray-900">{userDashboard.stats.pending_orders}</div>
            <p className="text-sm text-gray-600">Pending Orders</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="photos" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="photos">My Photos</TabsTrigger>
          <TabsTrigger value="bookings">Bookings</TabsTrigger>
          <TabsTrigger value="frames">Frame Orders</TabsTrigger>
          <TabsTrigger value="order-frame">Order Frame</TabsTrigger>
        </TabsList>

        <TabsContent value="photos" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Your Photo Gallery</CardTitle>
              <CardDescription>All photos from your sessions with Alostudio</CardDescription>
            </CardHeader>
            <CardContent>
              {userDashboard.photos.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {userDashboard.photos.map((photo) => (
                    <div 
                      key={photo.id} 
                      className={`relative aspect-square rounded-lg overflow-hidden cursor-pointer border-2 transition-all ${
                        selectedPhotos.includes(photo.id) 
                          ? 'border-pink-500 ring-2 ring-pink-200' 
                          : 'border-gray-200 hover:border-pink-300'
                      }`}
                      onClick={() => togglePhotoSelection(photo.id)}
                    >
                      <img 
                        src={photo.file_url} 
                        alt={photo.file_name}
                        className="w-full h-full object-cover"
                        onClick={(e) => {
                          e.stopPropagation();
                          onImageZoom && onImageZoom(photo);
                        }}
                      />
                      {selectedPhotos.includes(photo.id) && (
                        <div className="absolute inset-0 bg-pink-500 bg-opacity-20 flex items-center justify-center">
                          <CheckCircle className="w-6 h-6 text-pink-600" />
                        </div>
                      )}
                      <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white p-2">
                        <p className="text-xs truncate">{photo.file_name}</p>
                      </div>
                      <div className="absolute top-2 right-2">
                        <div className="bg-white bg-opacity-80 rounded-full p-1">
                          <ZoomIn className="w-4 h-4 text-gray-600" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <ImageIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Photos Yet</h3>
                  <p className="text-gray-600 mb-4">Book a session with us to start building your photo gallery!</p>
                  <Button 
                    className="bg-pink-600 hover:bg-pink-700"
                    onClick={onBookSession}
                  >
                    Book a Session
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bookings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Your Bookings</CardTitle>
              <CardDescription>History of all your sessions and appointments</CardDescription>
            </CardHeader>
            <CardContent>
              {userDashboard.bookings.length > 0 ? (
                <div className="space-y-4">
                  {userDashboard.bookings.map((booking) => (
                    <div key={booking.id} className="border rounded-lg p-4 bg-white shadow-sm">
                      <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                        <div className="flex-1">
                          <h3 className="font-semibold">{booking.service_type}</h3>
                          <p className="text-sm text-gray-600">Date: {new Date(booking.booking_date).toLocaleDateString()}</p>
                          <p className="text-sm text-gray-600">Time: {booking.booking_time}</p>
                          {booking.payment_amount && (
                            <p className="text-sm font-medium text-green-600">
                              Payment: ${booking.payment_amount}
                            </p>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          {getStatusBadge(booking.status)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Camera className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Bookings Yet</h3>
                  <p className="text-gray-600">Start by booking your first session with us!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="frames" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Frame Orders</CardTitle>
              <CardDescription>Your custom frame orders and their status</CardDescription>
            </CardHeader>
            <CardContent>
              {userDashboard.frame_orders.length > 0 ? (
                <div className="space-y-4">
                  {userDashboard.frame_orders.map((order) => (
                    <div key={order.id} className="border rounded-lg p-4 bg-white shadow-sm">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-semibold">Frame Order #{order.id.slice(0, 8)}</h3>
                          <p className="text-sm text-gray-600">Size: {order.frame_size} | Style: {order.frame_style}</p>
                          <p className="text-sm text-gray-600">Quantity: {order.quantity} | Photos: {order.photo_ids.length}</p>
                          <p className="text-sm font-medium">Total: ${order.total_price}</p>
                          {order.special_instructions && (
                            <p className="text-sm text-gray-600">Instructions: {order.special_instructions}</p>
                          )}
                        </div>
                        <div className="flex flex-col gap-2 items-end">
                          {getStatusBadge(order.status)}
                          {order.status === 'pending_payment' && (
                            <Button
                              size="sm"
                              onClick={() => handleFramePayment(order.id, order.total_price * 0.5)} // 50% deposit
                              className="bg-pink-600 hover:bg-pink-700"
                            >
                              Pay Deposit
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Package className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Frame Orders</h3>
                  <p className="text-gray-600">Order custom frames for your photos!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="order-frame" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Order Custom Frames</CardTitle>
              <CardDescription>
                {userDashboard.photos.length > 0 
                  ? "Select photos from your gallery and customize your frame order"
                  : "Upload photos to get custom frames made"
                }
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {userDashboard.photos.length > 0 ? (
                <>
                  {/* Photo Selection */}
                  <div>
                    <h3 className="text-lg font-medium mb-3">
                      Select Photos ({selectedPhotos.length} selected)
                    </h3>
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                      {userDashboard.photos.map((photo) => (
                        <div 
                          key={photo.id}
                          className={`relative aspect-square rounded-lg overflow-hidden cursor-pointer border-2 ${
                            selectedPhotos.includes(photo.id) 
                              ? 'border-pink-500 ring-2 ring-pink-200' 
                              : 'border-gray-200'
                          }`}
                          onClick={() => togglePhotoSelection(photo.id)}
                        >
                          <img 
                            src={photo.file_url} 
                            alt={photo.file_name}
                            className="w-full h-full object-cover"
                          />
                          {selectedPhotos.includes(photo.id) && (
                            <div className="absolute inset-0 bg-pink-500 bg-opacity-30 flex items-center justify-center">
                              <CheckCircle className="w-4 h-4 text-white" />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Frame Options */}
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="frame_size">Frame Size</Label>
                      <Select 
                        value={frameOrderForm.frame_size} 
                        onValueChange={(value) => setFrameOrderForm(prev => ({...prev, frame_size: value}))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select size" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="5x7">5x7 - $25</SelectItem>
                          <SelectItem value="8x10">8x10 - $45</SelectItem>
                          <SelectItem value="11x14">11x14 - $75</SelectItem>
                          <SelectItem value="16x20">16x20 - $120</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="frame_style">Frame Style</Label>
                      <Select 
                        value={frameOrderForm.frame_style} 
                        onValueChange={(value) => setFrameOrderForm(prev => ({...prev, frame_style: value}))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select style" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="modern">Modern</SelectItem>
                          <SelectItem value="classic">Classic</SelectItem>
                          <SelectItem value="rustic">Rustic</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="quantity">Quantity per Photo</Label>
                      <Input
                        id="quantity"
                        type="number"
                        min="1"
                        value={frameOrderForm.quantity}
                        onChange={(e) => setFrameOrderForm(prev => ({...prev, quantity: parseInt(e.target.value) || 1}))}
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="instructions">Special Instructions</Label>
                    <Textarea
                      id="instructions"
                      placeholder="Any special requests or instructions..."
                      value={frameOrderForm.special_instructions}
                      onChange={(e) => setFrameOrderForm(prev => ({...prev, special_instructions: e.target.value}))}
                    />
                  </div>

                  {/* Order Summary */}
                  {selectedPhotos.length > 0 && (
                    <div className="bg-pink-50 p-4 rounded-lg">
                      <h3 className="font-medium text-pink-900 mb-2">Order Summary</h3>
                      <div className="text-sm text-pink-800 space-y-1">
                        <p>Photos selected: {selectedPhotos.length}</p>
                        <p>Frame size: {frameOrderForm.frame_size}</p>
                        <p>Frame style: {frameOrderForm.frame_style}</p>
                        <p>Quantity per photo: {frameOrderForm.quantity}</p>
                        <p className="font-semibold text-lg">Total: ${calculateFrameTotal()}</p>
                        <p className="text-xs">50% deposit required: ${(calculateFrameTotal() * 0.5).toFixed(2)}</p>
                      </div>
                    </div>
                  )}

                  <Button 
                    onClick={handleFrameOrder}
                    disabled={selectedPhotos.length === 0}
                    className="w-full bg-pink-600 hover:bg-pink-700"
                  >
                    <ShoppingCart className="w-4 h-4 mr-2" />
                    Create Frame Order (${calculateFrameTotal()})
                  </Button>
                </>
              ) : (
                <div className="text-center py-12">
                  <ImageIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Photos Available</h3>
                  <p className="text-gray-600 mb-4">
                    You need to have photos with us first, or you can upload your own photos for custom framing.
                  </p>
                  <Button 
                    className="bg-pink-600 hover:bg-pink-700"
                    onClick={onBookSession}
                  >
                    Upload Photos for Framing
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};