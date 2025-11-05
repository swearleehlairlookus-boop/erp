"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Search, Plus, Edit, Wrench, AlertTriangle, CheckCircle, XCircle, Package, Loader2, Calendar, Trash2 } from "lucide-react"
import { apiService } from "@/lib/api-service"
import { useToast } from "@/hooks/use-toast"

interface MedicalAsset {
  id: number
  asset_tag: string
  serial_number: string
  asset_name: string
  category_id: number
  category_name?: string
  manufacturer: string
  model: string
  purchase_date: string
  warranty_expiry: string | null
  status: "Operational" | "Maintenance Required" | "Out of Service" | "Retired"
  location: string
  assigned_to: number | null
  last_maintenance_date: string | null
  next_maintenance_date: string | null
  maintenance_notes: string | null
  purchase_cost: number
  current_value: number
  created_at: string
  updated_at: string
}

interface AssetCategory {
  id: number
  category_name: string
  description: string
  requires_calibration: boolean
  calibration_frequency_months: number | null
}

interface AssetManagementProps {
  userRole: string
}

const assetStatuses = [
  { value: "Operational", label: "Operational", icon: CheckCircle, color: "bg-green-100 text-green-800" },
  {
    value: "Maintenance Required",
    label: "Maintenance Required",
    icon: Wrench,
    color: "bg-yellow-100 text-yellow-800",
  },
  { value: "Out of Service", label: "Out of Service", icon: XCircle, color: "bg-red-100 text-red-800" },
  { value: "Retired", label: "Retired", icon: AlertTriangle, color: "bg-gray-100 text-gray-800" },
]

export function AssetManagement({ userRole }: AssetManagementProps) {
  const [assets, setAssets] = useState<MedicalAsset[]>([])
  const [categories, setCategories] = useState<AssetCategory[]>([])
  // Debug: log userRole and asset statuses on mount
  useEffect(() => {
    console.log('Current userRole:', userRole)
    if (assets.length > 0) {
      console.log('Asset statuses:', assets.map(a => ({ id: a.id, status: a.status, name: a.asset_name })))
    }
  }, [userRole, assets])
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [categoryFilter, setCategoryFilter] = useState<string>("all")
  const [showAddForm, setShowAddForm] = useState(false)
  const [selectedAsset, setSelectedAsset] = useState<MedicalAsset | null>(null)
  const [showMaintenanceDialog, setShowMaintenanceDialog] = useState(false)
  const [maintenanceAsset, setMaintenanceAsset] = useState<MedicalAsset | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const { toast } = useToast()

  const [newAsset, setNewAsset] = useState({
    asset_name: "",
    asset_tag: "",
    serial_number: "",
    manufacturer: "",
    model: "",
    category_id: "",
    purchase_date: new Date().toISOString().split("T")[0],
    warranty_expiry: "",
    status: "Operational" as MedicalAsset["status"],
    location: "",
    purchase_cost: 0,
    current_value: 0,
    maintenance_notes: "",
  })

  const [maintenanceForm, setMaintenanceForm] = useState({
    last_maintenance_date: "",
    next_maintenance_date: "",
    maintenance_notes: "",
    maintenance_type: "preventive" as "preventive" | "corrective" | "calibration",
  })

  // Helper to normalize status strings from backend (case-insensitive and some variants)
  const normalizeStatus = (raw: any): MedicalAsset['status'] => {
    if (!raw && raw !== 0) return 'Operational'
    const s = String(raw).trim().toLowerCase()
    if (s === 'operational' || s === 'operational' ) return 'Operational'
    if (s === 'maintenance required' || s === 'maintenance_required' || s === 'maintenance-required' || s === 'maintenancerequired') return 'Maintenance Required'
    if (s === 'out of service' || s === 'out_of_service' || s === 'out-of-service' || s === 'outofservice') return 'Out of Service'
    if (s === 'retired') return 'Retired'
    // Fallback: capitalize first letter
    const capitalized = s.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
    if (['Operational','Maintenance Required','Out Of Service','Retired'].includes(capitalized)) {
      // Map 'Out Of Service' -> 'Out of Service'
      if (capitalized === 'Out Of Service') return 'Out of Service'
      return capitalized as MedicalAsset['status']
    }
    return 'Operational'
  }

  // Fetch assets from API
  const fetchAssets = async () => {
    try {
      setLoading(true)
      const response = await apiService.getAssets()
      if (response.success && response.data) {
        // Normalize incoming statuses so UI comparisons work regardless of backend casing/variants
        const incoming = (response.data as MedicalAsset[]) || []
        const mapped = incoming.map((a) => ({ ...a, status: normalizeStatus((a as any).status) }))
        console.debug('Fetched assets (normalized statuses):', mapped.map(m => ({ id: m.id, status: m.status })))
        setAssets(mapped)
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load assets",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Fetch categories from API
  const fetchCategories = async () => {
    try {
      const response = await apiService.getAssetCategories()
      if (response.success && response.data) {
        const cats = (response.data as AssetCategory[]) || []
        setCategories(cats)
        if (!newAsset.category_id && cats.length > 0) {
          setNewAsset((prev) => ({ ...prev, category_id: String(cats[0].id) }))
        }
      }
    } catch (e) {
      console.warn("Failed to fetch asset categories:", e)
    }
  }

  useEffect(() => {
    fetchAssets()
    fetchCategories()
  }, [])

  const filteredAssets = assets.filter((asset) => {
    const matchesSearch =
      asset.asset_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.manufacturer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.asset_tag.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus = statusFilter === "all" || asset.status === statusFilter
    const matchesCategory = categoryFilter === "all" || asset.category_id.toString() === categoryFilter

    return matchesSearch && matchesStatus && matchesCategory
  })

  const getStatusConfig = (status: MedicalAsset["status"]) => {
    return assetStatuses.find((s) => s.value === status) || assetStatuses[0]
  }

  const getMaintenanceAlert = (asset: MedicalAsset) => {
    if (!asset.next_maintenance_date) return null

    const today = new Date()
    const nextMaintenance = new Date(asset.next_maintenance_date)
    const daysUntilMaintenance = Math.ceil((nextMaintenance.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

    if (daysUntilMaintenance <= 0) {
      return (
        <Badge variant="destructive" className="text-xs">
          <AlertTriangle className="w-3 h-3 mr-1" />
          Overdue
        </Badge>
      )
    } else if (daysUntilMaintenance <= 7) {
      return (
        <Badge variant="destructive" className="text-xs">
          <AlertTriangle className="w-3 h-3 mr-1" />
          Due Soon
        </Badge>
      )
    } else if (daysUntilMaintenance <= 30) {
      return (
        <Badge variant="secondary" className="text-xs bg-yellow-100 text-yellow-800">
          <Wrench className="w-3 h-3 mr-1" />
          Due This Month
        </Badge>
      )
    }

    return null
  }

  const addAsset = async () => {
    if (!newAsset.asset_name || !newAsset.asset_tag || !newAsset.manufacturer) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      })
      return
    }

    const parsedCategoryId = Number.parseInt(newAsset.category_id)
    if (!parsedCategoryId || Number.isNaN(parsedCategoryId)) {
      toast({
        title: "Validation Error",
        description: "Please select a category",
        variant: "destructive",
      })
      return
    }

    try {
      setSubmitting(true)

      const assetPayload = {
        asset_name: newAsset.asset_name,
        asset_tag: newAsset.asset_tag,
        serial_number: newAsset.serial_number,
        manufacturer: newAsset.manufacturer,
        model: newAsset.model,
        category_id: parsedCategoryId,
        purchase_date: newAsset.purchase_date,
        warranty_expiry: newAsset.warranty_expiry || null,
        status: newAsset.status,
        location: newAsset.location,
        purchase_cost: newAsset.purchase_cost,
        current_value: newAsset.current_value,
        maintenance_notes: newAsset.maintenance_notes || null,
      }

      const response = await apiService.createAsset(assetPayload)

      if (response.success) {
        toast({
          title: "Success",
          description: "Asset added successfully",
        })

        setNewAsset({
          asset_name: "",
          asset_tag: "",
          serial_number: "",
          manufacturer: "",
          model: "",
          category_id: "",
          purchase_date: new Date().toISOString().split("T")[0],
          warranty_expiry: "",
          status: "Operational",
          location: "",
          purchase_cost: 0,
          current_value: 0,
          maintenance_notes: "",
        })
        setShowAddForm(false)
        fetchAssets()
      } else {
        toast({
          title: "Error",
          description: response.error || "Failed to add asset",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      })
    } finally {
      setSubmitting(false)
    }
  }

  const updateAssetStatus = async (assetId: number, newStatus: MedicalAsset["status"]) => {
    try {
      const response = await apiService.updateAssetStatus(assetId, {
        status: newStatus
      })

      if (response.success) {
        toast({
          title: "Success",
          description: `Asset status updated to ${newStatus}`,
        })
        fetchAssets()
      } else {
        toast({
          title: "Error",
          description: response.error || "Failed to update asset",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      })
    }
  }

  const openMaintenanceDialog = (asset: MedicalAsset) => {
    setMaintenanceAsset(asset)
    setMaintenanceForm({
      last_maintenance_date: asset.last_maintenance_date || "",
      next_maintenance_date: asset.next_maintenance_date || "",
      maintenance_notes: asset.maintenance_notes || "",
      maintenance_type: "preventive",
    })
    setShowMaintenanceDialog(true)
  }

  const scheduleMaintenance = async () => {
    if (!maintenanceAsset) return

    try {
      setSubmitting(true)

      // Map form fields to backend asset_maintenance fields
      const payload: any = {
        maintenance_type: maintenanceForm.maintenance_type, // must be 'preventive', 'corrective', or 'calibration'
        maintenance_date: maintenanceForm.last_maintenance_date || new Date().toISOString().slice(0, 10),
        next_due_date: maintenanceForm.next_maintenance_date || null,
        notes: maintenanceForm.maintenance_notes || null,
      }

      const response = await apiService.createAssetMaintenance(maintenanceAsset.id, payload)

      if (response.success) {
        toast({
          title: "Success",
          description: "Maintenance scheduled successfully",
        })
        setShowMaintenanceDialog(false)
        setMaintenanceAsset(null)
        setMaintenanceForm({
          last_maintenance_date: "",
          next_maintenance_date: "",
          maintenance_notes: "",
          maintenance_type: "preventive",
        })
        fetchAssets()
      } else {
        toast({
          title: "Error",
          description: response.error || "Failed to schedule maintenance",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      })
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading assets...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold bg-linear-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
            Asset Management
          </h2>
          <p className="text-muted-foreground mt-1">Track and manage medical equipment and assets</p>
        </div>
        {(userRole === "administrator" || userRole === "doctor" || userRole === "nurse" || userRole === "inventory_manager") && (
          <Button
            onClick={() => {
              setShowAddForm(true)
              fetchCategories()
            }}
            className="flex items-center gap-2 bg-linear-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg shadow-primary/30"
          >
            <Plus className="w-4 h-4" />
            Add Asset
          </Button>
        )}
      </div>

      <Card className="border-primary/10 shadow-lg shadow-primary/5">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Search by name, tag, serial number, manufacturer, or model..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {assetStatuses.map((status) => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Filter by category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((category) => (
                  <SelectItem key={category.id} value={category.id.toString()}>
                    {category.category_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {showAddForm && (
        <Card className="border-primary/20 shadow-xl shadow-primary/10">
          <CardHeader className="bg-linear-to-r from-primary/5 to-transparent border-b border-primary/10">
            <CardTitle className="text-xl">Add New Asset</CardTitle>
            <CardDescription>Register a new medical asset or equipment</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Asset Name *</Label>
                <Input
                  value={newAsset.asset_name}
                  onChange={(e) => setNewAsset({ ...newAsset, asset_name: e.target.value })}
                  placeholder="Enter asset name"
                />
              </div>

              <div className="space-y-2">
                <Label>Asset Tag *</Label>
                <Input
                  value={newAsset.asset_tag}
                  onChange={(e) => setNewAsset({ ...newAsset, asset_tag: e.target.value })}
                  placeholder="Enter asset tag"
                />
              </div>

              <div className="space-y-2">
                <Label>Serial Number</Label>
                <Input
                  value={newAsset.serial_number}
                  onChange={(e) => setNewAsset({ ...newAsset, serial_number: e.target.value })}
                  placeholder="Enter serial number"
                />
              </div>

              <div className="space-y-2">
                <Label>Manufacturer *</Label>
                <Input
                  value={newAsset.manufacturer}
                  onChange={(e) => setNewAsset({ ...newAsset, manufacturer: e.target.value })}
                  placeholder="Enter manufacturer"
                />
              </div>

              <div className="space-y-2">
                <Label>Model</Label>
                <Input
                  value={newAsset.model}
                  onChange={(e) => setNewAsset({ ...newAsset, model: e.target.value })}
                  placeholder="Enter model"
                />
              </div>

              <div className="space-y-2">
                <Label>Category</Label>
                <Select
                  value={newAsset.category_id}
                  onValueChange={(val) => setNewAsset({ ...newAsset, category_id: val })}
                  disabled={categories.length === 0}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue
                      placeholder={categories.length === 0 ? "No categories available" : "Select a category"}
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.length === 0 ? (
                      <SelectItem value="__no_categories__" disabled>
                        No categories found
                      </SelectItem>
                    ) : (
                      categories.map((c) => (
                        <SelectItem key={c.id} value={c.id.toString()}>
                          {c.category_name}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Purchase Cost (ZAR)</Label>
                <Input
                  type="number"
                  value={newAsset.purchase_cost}
                  onChange={(e) => setNewAsset({ ...newAsset, purchase_cost: Number.parseFloat(e.target.value) || 0 })}
                  placeholder="0"
                />
              </div>

              <div className="space-y-2">
                <Label>Current Value (ZAR)</Label>
                <Input
                  type="number"
                  value={newAsset.current_value}
                  onChange={(e) => setNewAsset({ ...newAsset, current_value: Number.parseFloat(e.target.value) || 0 })}
                  placeholder="0"
                />
              </div>

              <div className="space-y-2">
                <Label>Location</Label>
                <Input
                  value={newAsset.location}
                  onChange={(e) => setNewAsset({ ...newAsset, location: e.target.value })}
                  placeholder="Enter current location"
                />
              </div>

              <div className="space-y-2">
                <Label>Purchase Date</Label>
                <Input
                  type="date"
                  value={newAsset.purchase_date}
                  onChange={(e) => setNewAsset({ ...newAsset, purchase_date: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label>Warranty Expiry</Label>
                <Input
                  type="date"
                  value={newAsset.warranty_expiry}
                  onChange={(e) => setNewAsset({ ...newAsset, warranty_expiry: e.target.value })}
                />
              </div>

              <div className="space-y-2 md:col-span-2">
                <Label>Maintenance Notes</Label>
                <Input
                  value={newAsset.maintenance_notes}
                  onChange={(e) => setNewAsset({ ...newAsset, maintenance_notes: e.target.value })}
                  placeholder="Enter maintenance notes"
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button onClick={addAsset} disabled={submitting}>
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Add Asset
              </Button>
              <Button variant="outline" onClick={() => setShowAddForm(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Dialog open={showMaintenanceDialog} onOpenChange={setShowMaintenanceDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Schedule Maintenance</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label>Last Maintenance Date</Label>
              <Input
                type="date"
                value={maintenanceForm.last_maintenance_date}
                onChange={(e) => setMaintenanceForm({ ...maintenanceForm, last_maintenance_date: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>Next Maintenance Date</Label>
              <Input
                type="date"
                value={maintenanceForm.next_maintenance_date}
                onChange={(e) => setMaintenanceForm({ ...maintenanceForm, next_maintenance_date: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>Maintenance Notes</Label>
              <Input
                value={maintenanceForm.maintenance_notes}
                onChange={(e) => setMaintenanceForm({ ...maintenanceForm, maintenance_notes: e.target.value })}
                placeholder="Enter maintenance notes"
              />
            </div>

            <div className="space-y-2">
              <Label>Maintenance Type</Label>
              <Select
                value={maintenanceForm.maintenance_type}
                onValueChange={(val) => setMaintenanceForm({ ...maintenanceForm, maintenance_type: val as "preventive" | "corrective" | "calibration" })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="preventive">Preventive</SelectItem>
                  <SelectItem value="corrective">Corrective</SelectItem>
                  <SelectItem value="calibration">Calibration</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-2">
              <Button onClick={scheduleMaintenance} disabled={submitting}>
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Schedule
              </Button>
              <Button variant="outline" onClick={() => setShowMaintenanceDialog(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4">
        {filteredAssets.length === 0 ? (
          <Card className="border-primary/10">
            <CardContent className="pt-6 text-center">
              <p className="text-muted-foreground">No assets found matching your criteria.</p>
            </CardContent>
          </Card>
        ) : (
          filteredAssets.map((asset) => {
            const statusConfig = getStatusConfig(asset.status)
            const StatusIcon = statusConfig.icon
            const maintenanceAlert = getMaintenanceAlert(asset)
            return (
              <Card
                key={asset.id}
                className="hover:shadow-xl hover:shadow-primary/10 transition-all duration-300 border-primary/10 hover:border-primary/30 group"
              >
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="w-14 h-14 bg-linear-to-br from-primary/20 to-primary/5 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-primary/10">
                        <Package className="w-7 h-7 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-foreground">{asset.asset_name}</h3>
                          <Badge className={statusConfig.color}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {statusConfig.label}
                          </Badge>
                          {maintenanceAlert}
                        </div>
                        <div className="flex flex-wrap gap-2 mb-3">
                          <Badge variant="outline">Tag: {asset.asset_tag}</Badge>
                          <Badge variant="outline">SN: {asset.serial_number || "N/A"}</Badge>
                          {asset.category_name && <Badge variant="outline">{asset.category_name}</Badge>}
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 text-sm text-muted-foreground">
                          <div>
                            <strong>Manufacturer:</strong> {asset.manufacturer}
                          </div>
                          <div>
                            <strong>Model:</strong> {asset.model || "N/A"}
                          </div>
                          <div>
                            <strong>Location:</strong> {asset.location || "N/A"}
                          </div>
                          <div>
                            <strong>Purchase Cost:</strong> R{asset.purchase_cost?.toLocaleString() || 0}
                          </div>
                          <div>
                            <strong>Current Value:</strong> R{asset.current_value?.toLocaleString() || 0}
                          </div>
                          {asset.warranty_expiry && (
                            <div>
                              <strong>Warranty Expires:</strong> {new Date(asset.warranty_expiry).toLocaleDateString()}
                            </div>
                          )}
                          {asset.next_maintenance_date && (
                            <div className="sm:col-span-2 lg:col-span-3">
                              <strong>Next Maintenance:</strong>{" "}
                              {new Date(asset.next_maintenance_date).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    {/* Always render button group for debugging */}
                    <div className="flex gap-2 ml-4">
                      <Button variant="outline" size="sm" onClick={() => setSelectedAsset(asset)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => openMaintenanceDialog(asset)}
                        className="flex items-center gap-1"
                      >
                        <Calendar className="w-4 h-4" />
                        <span className="hidden sm:inline">Schedule Maintenance</span>
                      </Button>
                      {/* Wrench button for status change to Maintenance Required */}
                      {asset.status === "Operational" && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => updateAssetStatus(asset.id, "Maintenance Required")}
                          title="Mark as Maintenance Required"
                        >
                          <Wrench className="w-4 h-4" />
                        </Button>
                      )}
                      {/* CheckCircle button for status change back to Operational */}
                      {asset.status === "Maintenance Required" && (
                        <Button variant="outline" size="sm" onClick={() => updateAssetStatus(asset.id, "Operational")}> 
                          <CheckCircle className="w-4 h-4" />
                        </Button>
                      )}
                      {/* Delete button with Trash2 icon */}
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => {
                          if (window.confirm(`Are you sure you want to delete asset '${asset.asset_name}'?`)) {
                            // Implement deleteAsset function or logic here
                            toast({ title: "Delete not implemented", description: "Add deleteAsset logic.", variant: "destructive" })
                          }
                        }}
                        title="Delete Asset"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  {asset.maintenance_notes && (
                    <div className="border-t pt-3">
                      <p className="text-sm text-muted-foreground">
                        <strong>Maintenance Notes:</strong> {asset.maintenance_notes}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}