'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { getOrders } from '@/lib/api';
import type { Order } from '@/lib/types';

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const loadOrders = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filterStatus !== 'all') params.status = filterStatus;
      if (searchTerm) params.market_id = searchTerm;

      const data = await getOrders(params);
      setOrders(data);
    } catch (err) {
      console.error('Failed to load orders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, [filterStatus, searchTerm]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'filled': return 'text-green-600 dark:text-green-400';
      case 'cancelled': return 'text-red-600 dark:text-red-400';
      case 'expired': return 'text-yellow-600 dark:text-yellow-400';
      default: return 'text-blue-600 dark:text-blue-400';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'filled': return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200';
      case 'cancelled': return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
      case 'expired': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200';
      default: return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200';
    }
  };

  const filteredOrders = orders.filter(order =>
    filterStatus === 'all' || order.status === filterStatus
  );

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <h1 className="text-4xl font-bold">Orders</h1>
        <div className="flex gap-4 w-full md:w-auto">
          <Input
            placeholder="Search by market ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full md:w-64"
          />
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="filled">Filled</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
              <SelectItem value="expired">Expired</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-muted-foreground">Loading orders...</div>
          </CardContent>
        </Card>
      ) : filteredOrders.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-muted-foreground">No orders found</div>
          </CardContent>
        </Card>
      ) : (
        <div className="rounded-lg border bg-background">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Order ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Market</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Type</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Price</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Size</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Filled</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Created</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map(order => (
                  <tr key={order.id} className="border-b hover:bg-muted/50 transition-colors">
                    <td className="px-4 py-3 text-sm">
                      <span className="font-mono text-xs">{order.id.slice(-8)}</span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className="font-mono text-xs">{order.market_id ? order.market_id.slice(-8) : 'N/A'}</span>
                    </td>
                    <td className="px-4 py-3 text-sm font-medium capitalize">{order.order_type}</td>
                    <td className="px-4 py-3 text-sm font-mono">{(order.price * 100).toFixed(1)}¢</td>
                    <td className="px-4 py-3 text-sm font-medium">{order.size.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm font-medium">{order.filled_size.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(order.status)}`}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {new Date(order.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
