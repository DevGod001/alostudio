import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { DollarSign, TrendingUp, Calendar, CreditCard } from 'lucide-react';

export const AdminWallet = ({ earnings }) => {
  if (!earnings || Object.keys(earnings).length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-gray-500">Loading earnings data...</p>
        </CardContent>
      </Card>
    );
  }

  const formatCurrency = (amount) => `$${amount.toFixed(2)}`;

  const getServiceColor = (serviceType) => {
    const colors = {
      'makeup': 'bg-pink-100 text-pink-800',
      'photography': 'bg-blue-100 text-blue-800',
      'video': 'bg-purple-100 text-purple-800',
      'combo': 'bg-green-100 text-green-800',
      'editing': 'bg-yellow-100 text-yellow-800',
      'frames': 'bg-indigo-100 text-indigo-800',
      'graphic_design': 'bg-red-100 text-red-800'
    };
    return colors[serviceType] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Earnings Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Earnings</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(earnings.total_earnings)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Recent (30 days)</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(earnings.recent_earnings)}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Transaction</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(earnings.stats.average_transaction)}
                </p>
              </div>
              <CreditCard className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Transactions</p>
                <p className="text-2xl font-bold text-gray-900">
                  {earnings.stats.total_transactions}
                </p>
              </div>
              <Calendar className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Service Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Earnings by Service</CardTitle>
            <CardDescription>Revenue breakdown by service type</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(earnings.service_breakdown || {}).map(([serviceType, amount]) => (
                <div key={serviceType} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge className={getServiceColor(serviceType)}>
                      {serviceType.replace('_', ' ').toUpperCase()}
                    </Badge>
                  </div>
                  <span className="font-semibold">{formatCurrency(amount)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Transactions</CardTitle>
            <CardDescription>Latest earnings from bookings and orders</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-80 overflow-y-auto">
              {earnings.earnings_history?.slice(0, 10).map((earning) => (
                <div key={earning.id} className="flex items-center justify-between py-2 border-b border-gray-100">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge className={getServiceColor(earning.service_type)} size="sm">
                        {earning.service_type.replace('_', ' ')}
                      </Badge>
                      <span className="text-sm text-gray-500">
                        {new Date(earning.payment_date).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      ID: {earning.booking_id.slice(0, 8)}
                    </p>
                  </div>
                  <span className="font-semibold text-green-600">
                    +{formatCurrency(earning.amount)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Earnings Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Earnings Trend</CardTitle>
          <CardDescription>Monthly earnings performance</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center">
              <TrendingUp className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Earnings chart coming soon</p>
              <p className="text-sm text-gray-400">Track your monthly performance</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};