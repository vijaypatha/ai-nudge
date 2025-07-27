'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { formatInTimeZone } from 'date-fns-tz';
import { 
  TrendingUp, 
  Home, 
  DollarSign, 
  Calendar, 
  MapPin, 
  Square, 
  ChevronDown, 
  ChevronUp,
  Filter,
  SortAsc,
  SortDesc,
  Eye,
  EyeOff,
  X,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2
} from 'lucide-react';

interface MarketEvent {
  id: string;
  event_type: string;
  entity_id: string;
  payload: any;
  created_at: string;
  status: string;
  market_area: string;
}

interface SortOption {
  label: string;
  value: string;
}

interface GroupOption {
  label: string;
  value: string;
}

export default function MarketActivityPage() {
  const { api, user } = useAppContext();
  const router = useRouter();
  const [marketEvents, setMarketEvents] = useState<MarketEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<MarketEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // UI State
  const [expandedDescriptions, setExpandedDescriptions] = useState<string[]>([]);
  const [expandedFeatures, setExpandedFeatures] = useState<string[]>([]);
  const [photoGalleryOpen, setPhotoGalleryOpen] = useState(false);
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);
  const [currentEventPhotos, setCurrentEventPhotos] = useState<string[]>([]);
  const [isFullScreen, setIsFullScreen] = useState(false);
  
  // Filtering and Sorting
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [groupBy, setGroupBy] = useState<string>('none');
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');
  const [priceRangeFilter, setPriceRangeFilter] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Redirect non-realtors to dashboard
  useEffect(() => {
    if (user && user.user_type !== 'realtor') {
      router.push('/dashboard');
    }
  }, [user, router]);

  const fetchMarketActivity = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await api.get('/api/market-activity?limit=1000'); // Get all properties
      setMarketEvents(data);
      setFilteredEvents(data);
    } catch (err) {
      console.error('Failed to fetch market activity:', err);
      setError('Failed to load market activity data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketActivity();
  }, [api]);

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...marketEvents];

    // Apply event type filter
    if (eventTypeFilter !== 'all') {
      filtered = filtered.filter(event => event.event_type === eventTypeFilter);
    }

    // Apply price range filter
    if (priceRangeFilter !== 'all') {
      filtered = filtered.filter(event => {
        const price = event.payload?.StandardFields?.ListPrice || 0;
        switch (priceRangeFilter) {
          case 'under_500k':
            return price < 500000;
          case '500k_to_1m':
            return price >= 500000 && price < 1000000;
          case 'over_1m':
            return price >= 1000000;
          default:
            return true;
        }
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortBy) {
        case 'created_at':
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
          break;
        case 'price':
          aValue = a.payload?.StandardFields?.ListPrice || 0;
          bValue = b.payload?.StandardFields?.ListPrice || 0;
          break;
        case 'beds':
          aValue = a.payload?.StandardFields?.BedsTotal || 0;
          bValue = b.payload?.StandardFields?.BedsTotal || 0;
          break;
        case 'sqft':
          aValue = a.payload?.StandardFields?.AboveGradeFinishedArea || 0;
          bValue = b.payload?.StandardFields?.AboveGradeFinishedArea || 0;
          break;
        case 'year_built':
          aValue = a.payload?.StandardFields?.YearBuilt || 0;
          bValue = b.payload?.StandardFields?.YearBuilt || 0;
          break;
        default:
          aValue = a[sortBy as keyof MarketEvent];
          bValue = b[sortBy as keyof MarketEvent];
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredEvents(filtered);
  }, [marketEvents, sortBy, sortOrder, eventTypeFilter, priceRangeFilter]);

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return formatInTimeZone(date, Intl.DateTimeFormat().resolvedOptions().timeZone, "MMM d, h:mm a");
    } catch (e) {
      console.error("Time formatting failed:", e);
      return timestamp;
    }
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'new_listing':
        return <Home className="w-4 h-4 text-green-400" />;
      case 'price_change':
        return <DollarSign className="w-4 h-4 text-yellow-400" />;
      case 'sold_listing':
        return <TrendingUp className="w-4 h-4 text-blue-400" />;
      case 'content_suggestion':
        return <Calendar className="w-4 h-4 text-indigo-400" />;
      case 'appointment_reminder':
      case 'follow_up':
        return <Calendar className="w-4 h-4 text-orange-400" />;
      case 'new_opportunity':
        return <TrendingUp className="w-4 h-4 text-green-400" />;
      default:
        return <Calendar className="w-4 h-4 text-gray-400" />;
    }
  };

  const getEventLabel = (eventType: string) => {
    switch (eventType) {
      case 'new_listing':
        return 'New Listing';
      case 'price_change':
        return 'Price Change';
      case 'sold_listing':
        return 'Sold';
      case 'back_on_market':
        return 'Back on Market';
      case 'expired_listing':
        return 'Expired';
      case 'coming_soon':
        return 'Coming Soon';
      case 'withdrawn_listing':
        return 'Withdrawn';
      case 'content_suggestion':
        return 'Content Suggestion';
      case 'appointment_reminder':
        return 'Appointment Reminder';
      case 'follow_up':
        return 'Follow Up';
      case 'new_opportunity':
        return 'New Opportunity';
      default:
        return eventType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  };

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'new_listing':
      case 'new_opportunity':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'price_change':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'sold_listing':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'back_on_market':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'expired_listing':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'content_suggestion':
        return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
      case 'appointment_reminder':
      case 'follow_up':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const toggleDescription = (eventId: string) => {
    setExpandedDescriptions(prev => 
      prev.includes(eventId) 
        ? prev.filter(id => id !== eventId)
        : [...prev, eventId]
    );
  };

  const toggleFeatures = (eventId: string) => {
    setExpandedFeatures(prev => 
      prev.includes(eventId) 
        ? prev.filter(id => id !== eventId)
        : [...prev, eventId]
    );
  };

  const openPhotoGallery = (event: MarketEvent) => {
    const photos = getPropertyPhotos(event.payload?.StandardFields);
    if (photos.length > 0) {
      setCurrentEventPhotos(photos);
      setCurrentPhotoIndex(0);
      setPhotoGalleryOpen(true);
    }
  };

  const closePhotoGallery = () => {
    setPhotoGalleryOpen(false);
    setCurrentPhotoIndex(0);
    setCurrentEventPhotos([]);
  };

  const nextPhoto = () => {
    setCurrentPhotoIndex(prev => 
      prev < currentEventPhotos.length - 1 ? prev + 1 : 0
    );
  };

  const previousPhoto = () => {
    setCurrentPhotoIndex(prev => 
      prev > 0 ? prev - 1 : currentEventPhotos.length - 1
    );
  };

  const getPropertyPhotos = (standardFields: any): string[] => {
    if (!standardFields?.Media) {
      // No photos available from MLS API
      return [];
    }
    
    // Extract photo URLs from Media array
    const photos = standardFields.Media
      .filter((media: any) => media.MediaCategory === 'Photo' || media.Category === 'Photo')
      .map((media: any) => media.MediaURL || media.URL || media.Url);
    
    return photos.filter((url: string | undefined | null) => url); // Filter out any null/undefined URLs
  };

  const getMainPhotoUrl = (standardFields: any): string => {
    const photos = getPropertyPhotos(standardFields);
    return photos.length > 0 ? photos[0] : 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgdmlld0JveD0iMCAwIDQwMCAzMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjMzc0MTUxIi8+CjxwYXRoIGQ9Ik0xMDAgMTAwSDEwMFYyMDBIMTAwWiIgZmlsbD0iIzYyNzM4NCIvPgo8cGF0aCBkPSJNMTUwIDEwMEgyNTBWMjAwSDE1MFoiIGZpbGw9IiM2MjczODQiLz4KPHRleHQgeD0iMjAwIiB5PSIyNTAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzlDQTNBRiIgdGV4dC1hbmNob3I9Im1pZGRsZSI+UHJvcGVydHkgSW1hZ2U8L3RleHQ+Cjwvc3ZnPgo=';
  };

  const getPropertyFeatures = (standardFields: any): string[] => {
    const features = [];
    
    if (standardFields?.GarageSpaces) {
      features.push(`${standardFields.GarageSpaces}-car garage`);
    }
    if (standardFields?.PoolPrivateYN === 'Y') {
      features.push('Private pool');
    }
    if (standardFields?.FireplaceYN === 'Y') {
      features.push('Fireplace');
    }
    if (standardFields?.CentralAirYN === 'Y') {
      features.push('Central air');
    }
    if (standardFields?.HeatingYN === 'Y') {
      features.push('Heating');
    }
    if (standardFields?.CoolingYN === 'Y') {
      features.push('Cooling');
    }
    
    return features;
  };

  const sortOptions: SortOption[] = [
    { label: 'Newest First', value: 'created_at' },
    { label: 'Price: High to Low', value: 'price' },
    { label: 'Price: Low to High', value: 'price_asc' },
    { label: 'Bedrooms', value: 'beds' },
    { label: 'Square Footage', value: 'sqft' },
    { label: 'Year Built', value: 'year_built' },
  ];

  const groupOptions: GroupOption[] = [
    { label: 'No Grouping', value: 'none' },
    { label: 'By Event Type', value: 'event_type' },
    { label: 'By Price Range', value: 'price_range' },
    { label: 'By Bedrooms', value: 'beds' },
  ];

  const eventTypeOptions = [
    { label: 'All Events', value: 'all' },
    { label: 'New Listings', value: 'new_listing' },
    { label: 'Price Changes', value: 'price_change' },
    { label: 'Sold Properties', value: 'sold_listing' },
    { label: 'Back on Market', value: 'back_on_market' },
  ];

  const priceRangeOptions = [
    { label: 'All Prices', value: 'all' },
    { label: 'Under $500k', value: 'under_500k' },
    { label: '$500k - $1M', value: '500k_to_1m' },
    { label: 'Over $1M', value: 'over_1m' },
  ];

  const groupedEvents = () => {
    if (groupBy === 'none') {
      return { 'All Properties': filteredEvents };
    }

    const groups: { [key: string]: MarketEvent[] } = {};

    filteredEvents.forEach(event => {
      let groupKey = 'Other';

      switch (groupBy) {
        case 'event_type':
          groupKey = getEventLabel(event.event_type);
          break;
        case 'price_range':
          const price = event.payload?.StandardFields?.ListPrice || 0;
          if (price < 500000) groupKey = 'Under $500k';
          else if (price < 1000000) groupKey = '$500k - $1M';
          else groupKey = 'Over $1M';
          break;
        case 'beds':
          const beds = event.payload?.StandardFields?.BedsTotal || 0;
          if (beds <= 2) groupKey = '1-2 Bedrooms';
          else if (beds <= 4) groupKey = '3-4 Bedrooms';
          else groupKey = '5+ Bedrooms';
          break;
      }

      if (!groups[groupKey]) groups[groupKey] = [];
      groups[groupKey].push(event);
    });

    return groups;
  };

  return (
    <main className="flex-1 p-6 sm:p-8 overflow-y-auto">
      <header className="mb-8">
        <h1 className="text-4xl sm:text-5xl font-bold text-brand-white tracking-tight">Live Market Activity</h1>
        <p className="text-brand-text-muted mt-2 text-lg">Real-time market events and business opportunities from your integrated data sources.</p>
        
        {/* Stats */}
        <div className="mt-4 flex flex-wrap gap-4 text-sm text-brand-text-muted">
          <span>{filteredEvents.length} properties</span>
          <span>•</span>
          <span>{new Set(filteredEvents.map(e => e.event_type)).size} event types</span>
          <span>•</span>
          <span>Last updated: {filteredEvents.length > 0 ? formatTime(filteredEvents[0].created_at) : 'Never'}</span>
        </div>
      </header>

      {/* Filters and Sorting */}
      <div className="mb-6 bg-white/5 border border-white/10 rounded-lg p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-3 py-2 bg-brand-accent/10 text-brand-accent rounded-lg hover:bg-brand-accent/20 transition-colors"
          >
            <Filter className="w-4 h-4" />
            {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            Filters
          </button>

          {/* Sort */}
          <select
            value={`${sortBy}_${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('_');
              setSortBy(field);
              setSortOrder(order as 'asc' | 'desc');
            }}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"
          >
            {sortOptions.map(option => (
              <option key={option.value} value={`${option.value}_desc`}>
                {option.label}
              </option>
            ))}
          </select>

          {/* Group By */}
          <select
            value={groupBy}
            onChange={(e) => setGroupBy(e.target.value)}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"
          >
            {groupOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Expanded Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Event Type Filter */}
            <div>
              <label className="block text-sm font-medium text-brand-text-muted mb-2">
                Event Type
              </label>
              <select
                value={eventTypeFilter}
                onChange={(e) => setEventTypeFilter(e.target.value)}
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"
              >
                {eventTypeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Price Range Filter */}
            <div>
              <label className="block text-sm font-medium text-brand-text-muted mb-2">
                Price Range
              </label>
              <select
                value={priceRangeFilter}
                onChange={(e) => setPriceRangeFilter(e.target.value)}
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"
              >
                {priceRangeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Clear Filters */}
            <div className="flex items-end">
              <button
                onClick={() => {
                  setEventTypeFilter('all');
                  setPriceRangeFilter('all');
                }}
                className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
              >
                Clear Filters
              </button>
            </div>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-accent mx-auto mb-4"></div>
            <p className="text-brand-text-muted">Loading market activity...</p>
          </div>
        </div>
      ) : error ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-red-400 mb-4">
              <TrendingUp className="w-16 h-16 mx-auto opacity-50" />
            </div>
            <p className="text-lg font-medium text-brand-text-main mb-2">Failed to load market activity</p>
            <p className="text-sm text-brand-text-muted">{error}</p>
            <button 
              onClick={fetchMarketActivity}
              className="mt-4 px-4 py-2 bg-brand-accent text-brand-dark rounded-lg hover:brightness-110 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      ) : filteredEvents.length > 0 ? (
        <div className="space-y-8">
          {Object.entries(groupedEvents()).map(([groupName, events]) => (
            <div key={groupName}>
              {groupBy !== 'none' && (
                <h2 className="text-xl font-semibold text-brand-text-main mb-4 sticky top-0 bg-brand-dark/80 backdrop-blur-sm py-2 z-10">
                  {groupName} ({events.length})
                </h2>
              )}
              
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {events.map((event) => (
                  <div key={event.id} className="bg-white/5 border border-white/10 rounded-lg overflow-hidden hover:bg-white/10 transition-colors">
                    {/* Header */}
                    <div className="p-4 border-b border-white/10">
                      <div className="flex items-center gap-3 mb-3">
                        {getEventIcon(event.event_type)}
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getEventColor(event.event_type)}`}>
                          {getEventLabel(event.event_type)}
                        </span>
                        <span className="text-xs text-brand-text-muted">
                          {formatTime(event.created_at)}
                        </span>
                      </div>
                      
                      <h3 className="font-medium text-brand-text-main mb-2">
                        {event.payload?.StandardFields?.UnparsedAddress || 'Unknown Address'}
                      </h3>
                    </div>

                    {/* Photo Gallery */}
                    {event.payload?.StandardFields?.PhotosCount > 0 && (
                      <div className="relative">
                        <div className="h-48 bg-gray-800 overflow-hidden flex items-center justify-center">
                          <div className="text-center text-gray-400">
                            <div className="w-16 h-16 mx-auto mb-2">
                              <svg className="w-full h-full" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <p className="text-sm font-medium">Photos Available</p>
                            <p className="text-xs">{event.payload?.StandardFields?.PhotosCount} photos</p>
                            <p className="text-xs mt-1 text-gray-500">(Not yet integrated)</p>
                          </div>
                          <div className="absolute top-2 right-2 bg-black/50 px-2 py-1 rounded text-xs text-white">
                            {event.payload?.StandardFields?.PhotosCount} photos
                          </div>
                        </div>
                        <button 
                          onClick={() => openPhotoGallery(event)}
                          className="absolute bottom-2 left-2 bg-black/50 px-2 py-1 rounded text-xs text-white hover:bg-black/70 transition-colors"
                          disabled
                        >
                          Coming Soon
                        </button>
                      </div>
                    )}

                    {/* Property Details */}
                    <div className="p-4">
                      {/* Enhanced Details Grid */}
                      <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="flex items-center gap-2">
                          <DollarSign className="w-4 h-4 text-brand-accent" />
                          <span className="font-semibold text-brand-accent">
                            ${(event.payload?.StandardFields?.ListPrice || 0).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Home className="w-4 h-4 text-brand-text-muted" />
                          <span className="text-sm text-brand-text-muted">
                            {event.payload?.StandardFields?.BedsTotal || 0} bed, {event.payload?.StandardFields?.BathroomsTotalInteger || 0} bath
                          </span>
                        </div>
                        {event.payload?.StandardFields?.AboveGradeFinishedArea && (
                          <div className="flex items-center gap-2">
                            <Square className="w-4 h-4 text-brand-text-muted" />
                            <span className="text-sm text-brand-text-muted">
                              {event.payload.StandardFields.AboveGradeFinishedArea} sq ft
                            </span>
                          </div>
                        )}
                        {event.payload?.StandardFields?.YearBuilt && (
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-brand-text-muted" />
                            <span className="text-sm text-brand-text-muted">
                              Built {event.payload.StandardFields.YearBuilt}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Expandable Description */}
                      {event.payload?.StandardFields?.PublicRemarks && (
                        <div className="mb-4">
                          <button 
                            onClick={() => toggleDescription(event.id)}
                            className="text-sm text-brand-accent hover:underline flex items-center gap-1"
                          >
                            {expandedDescriptions.includes(event.id) ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                            {expandedDescriptions.includes(event.id) ? 'Hide description' : 'Show description'}
                          </button>
                                                     {expandedDescriptions.includes(event.id) && (
                             <p className="mt-2 text-sm text-brand-text-muted leading-relaxed overflow-hidden text-ellipsis">
                               {event.payload.StandardFields.PublicRemarks}
                             </p>
                           )}
                        </div>
                      )}

                      {/* Property Features */}
                      {getPropertyFeatures(event.payload?.StandardFields).length > 0 && (
                        <div className="mb-4">
                          <button 
                            onClick={() => toggleFeatures(event.id)}
                            className="text-sm text-brand-accent hover:underline flex items-center gap-1"
                          >
                            {expandedFeatures.includes(event.id) ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            {expandedFeatures.includes(event.id) ? 'Hide features' : 'Show features'}
                          </button>
                          {expandedFeatures.includes(event.id) && (
                            <div className="mt-2 grid grid-cols-1 gap-1">
                              {getPropertyFeatures(event.payload?.StandardFields).map((feature, index) => (
                                <div key={index} className="text-xs text-brand-text-muted flex items-center gap-1">
                                  <span className="w-1 h-1 bg-brand-accent rounded-full"></span>
                                  {feature}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Agent Info */}
                      <div className="flex items-center justify-between text-xs text-brand-text-muted pt-2 border-t border-white/10">
                        <span>Agent: {event.payload?.StandardFields?.ListAgentName || 'Unknown'}</span>
                        <span>MLS: {event.payload?.StandardFields?.ListingId || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <TrendingUp className="w-16 h-16 mb-4 mx-auto opacity-50" />
            <h2 className="text-lg font-medium mb-2">No market activity found</h2>
            <p className="text-sm text-brand-text-muted">Try adjusting your filters or check back later for new market events.</p>
          </div>
        </div>
      )}

      {/* Photo Gallery Modal */}
      {photoGalleryOpen && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900">Property Photos</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsFullScreen(!isFullScreen)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </button>
                <button
                  onClick={closePhotoGallery}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Main Photo */}
            <div className="relative bg-gray-900">
              <img 
                src={currentEventPhotos[currentPhotoIndex]} 
                alt={`Photo ${currentPhotoIndex + 1}`}
                className={`w-full object-cover ${isFullScreen ? 'h-[80vh]' : 'h-96'}`}
              />
              
              {/* Navigation */}
              <button 
                onClick={previousPhoto}
                className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
              <button 
                onClick={nextPhoto}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
              >
                <ChevronRight className="w-6 h-6" />
              </button>
              
              {/* Photo Counter */}
              <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black/50 text-white px-3 py-1 rounded-full text-sm">
                {currentPhotoIndex + 1} / {currentEventPhotos.length}
              </div>
            </div>
            
            {/* Thumbnails */}
            <div className="p-4">
              <div className="flex gap-2 overflow-x-auto">
                {currentEventPhotos.map((photo, index) => (
                  <img 
                    key={index}
                    src={photo}
                    alt={`Thumbnail ${index + 1}`}
                    className={`w-16 h-16 object-cover rounded cursor-pointer transition-all ${
                      index === currentPhotoIndex 
                        ? 'ring-2 ring-brand-accent scale-110' 
                        : 'hover:scale-105'
                    }`}
                    onClick={() => setCurrentPhotoIndex(index)}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
} 