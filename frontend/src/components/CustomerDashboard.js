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
import { CheckCircle, Camera, Package, Clock, Image as ImageIcon, ShoppingCart, ZoomIn, Download } from 'lucide-react';

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
  onImageZoom,
  onImageDownload
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
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-4">
          <TabsTrigger value="photos" className="text-xs md:text-sm">My Photos</TabsTrigger>
          <TabsTrigger value="bookings" className="text-xs md:text-sm">Bookings</TabsTrigger>
          <TabsTrigger value="frames" className="text-xs md:text-sm">Frame Orders</TabsTrigger>
          <TabsTrigger value="order-frame" className="text-xs md:text-sm">Order Frame</TabsTrigger>
        </TabsList>

        <TabsContent value="photos" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>My Photos</CardTitle>
              <CardDescription>Your session photos and uploaded images</CardDescription>
            </CardHeader>
            <CardContent>
              {userDashboard.photos && userDashboard.photos.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {userDashboard.photos.map((photo) => (
                    <div 
                      key={photo.id} 
                      className="relative aspect-square rounded-lg overflow-hidden border border-gray-200 hover:border-pink-300 transition-all group cursor-pointer"
                      onClick={() => onImageZoom && onImageZoom(photo)}
                    >
                      <img 
                        src={photo.file_url} 
                        alt={photo.file_name}
                        className="w-full h-full object-cover transition-transform group-hover:scale-105"
                      />
                      
                      {/* Download Button */}
                      <div className="absolute top-2 right-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onImageDownload && onImageDownload(photo);
                          }}
                          className="bg-white bg-opacity-90 hover:bg-white rounded-full p-2 shadow-lg transition-all hover:scale-110"
                          title="Download image"
                        >
                          <Download className="w-4 h-4 text-gray-700" />
                        </button>
                      </div>
                      
                      {/* Zoom Indicator */}
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all flex items-center justify-center pointer-events-none">
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <ZoomIn className="w-8 h-8 text-white drop-shadow-lg" />
                        </div>
                      </div>
                      
                      {/* Image Info */}
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent text-white p-3">
                        <p className="text-sm font-medium truncate">{photo.file_name}</p>
                        <p className="text-xs text-gray-300">
                          {photo.photo_type === 'session' && photo.uploaded_by_admin ? 'Session Photo' : 'Uploaded'}
                        </p>
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
              <CardDescription>Select photos, customize frames, and complete payment</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {userDashboard.photos && userDashboard.photos.length > 0 ? (
                <>
                  {/* Photo Selection */}
                  <div>
                    <Label className="text-base font-medium mb-3 block">Select Photos ({selectedPhotos.length} selected)</Label>
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
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
                          />
                          {selectedPhotos.includes(photo.id) && (
                            <div className="absolute inset-0 bg-pink-500 bg-opacity-30 flex items-center justify-center">
                              <CheckCircle className="w-6 h-6 text-white" />
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
                        onValueChange={(value) => setFrameOrderForm(prev => ({ ...prev, frame_size: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Choose size" />
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
                        onValueChange={(value) => setFrameOrderForm(prev => ({ ...prev, frame_style: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Choose style" />
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
                        type="number"
                        min="1"
                        value={frameOrderForm.quantity}
                        onChange={(e) => setFrameOrderForm(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))}
                      />
                    </div>
                  </div>

                  {/* Delivery Options */}
                  <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
                    <Label className="text-base font-medium">Delivery Options</Label>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          id="self_pickup"
                          name="delivery"
                          value="self_pickup"
                          checked={frameOrderForm.delivery_method === 'self_pickup'}
                          onChange={(e) => setFrameOrderForm(prev => ({ ...prev, delivery_method: e.target.value }))}
                          className="h-4 w-4 text-pink-600"
                        />
                        <Label htmlFor="self_pickup" className="flex-1">
                          <span className="font-medium">Self Pickup</span> - Free
                          <span className="block text-sm text-gray-600">Pick up from our studio</span>
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          id="ship_to_me"
                          name="delivery"
                          value="ship_to_me"
                          checked={frameOrderForm.delivery_method === 'ship_to_me'}
                          onChange={(e) => setFrameOrderForm(prev => ({ ...prev, delivery_method: e.target.value }))}
                          className="h-4 w-4 text-pink-600"
                        />
                        <Label htmlFor="ship_to_me" className="flex-1">
                          <span className="font-medium">Ship to Me</span> - Delivery fee will be added
                          <span className="block text-sm text-gray-600">We'll deliver to your address</span>
                        </Label>
                      </div>
                    </div>

                    {frameOrderForm.delivery_method === 'ship_to_me' && (
                      <div>
                        <Label htmlFor="delivery_address">Delivery Address</Label>
                        <textarea
                          id="delivery_address"
                          value={frameOrderForm.delivery_address}
                          onChange={(e) => setFrameOrderForm(prev => ({ ...prev, delivery_address: e.target.value }))}
                          placeholder="Enter your complete delivery address..."
                          className="w-full p-2 border border-gray-300 rounded-md focus:ring-pink-500 focus:border-pink-500"
                          rows="3"
                        />
                      </div>
                    )}
                  </div>

                  {/* Order Summary */}
                  <div className="bg-pink-50 p-4 rounded-lg">
                    <h4 className="font-medium mb-2">Order Summary</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>{selectedPhotos.length} photos × {frameOrderForm.quantity} frames each</span>
                        <span>${calculateFramePrice(frameOrderForm.frame_size, frameOrderForm.quantity * selectedPhotos.length)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Frame Size: {frameOrderForm.frame_size}</span>
                        <span>Style: {frameOrderForm.frame_style}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Delivery: {frameOrderForm.delivery_method === 'self_pickup' ? 'Self Pickup (Free)' : 'Ship to Me (+delivery fee)'}</span>
                      </div>
                      <div className="flex justify-between font-medium pt-2 border-t">
                        <span>Total:</span>
                        <span>${calculateFramePrice(frameOrderForm.frame_size, frameOrderForm.quantity * selectedPhotos.length)}</span>
                      </div>
                      {frameOrderForm.delivery_method === 'ship_to_me' && (
                        <p className="text-xs text-gray-600 mt-1">
                          *Delivery fee will be calculated and added by admin based on your address
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Create Order Button */}
                  <Button 
                    onClick={handleFrameOrder} 
                    className="w-full bg-pink-600 hover:bg-pink-700 text-white py-3"
                    disabled={selectedPhotos.length === 0 || !frameOrderForm.frame_size || !frameOrderForm.frame_style || !frameOrderForm.delivery_method}
                  >
                    Proceed to Payment - ${calculateFramePrice(frameOrderForm.frame_size, frameOrderForm.quantity * selectedPhotos.length)}
                  </Button>
                </>
              ) : (
                <div className="text-center py-12">
                  <Package className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Photos Available</h3>
                  <p className="text-gray-600 mb-4">You need photos in your gallery before you can order frames.</p>
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
      </Tabs>
    </div>
  );
};