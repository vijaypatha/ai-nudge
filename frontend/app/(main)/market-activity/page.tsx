'use client';

import { useState, useEffect, useMemo, FC } from 'react';
import { useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { formatInTimeZone } from 'date-fns-tz';
import { 
  Home, DollarSign, BedDouble, Bath, Square, Calendar, Link as LinkIcon,
  Filter, X, Image as ImageIcon, ChevronLeft, ChevronRight, List
} from 'lucide-react';

// --- TYPE DEFINITIONS ---
interface MarketEvent {
  id: string;
  event_type: string;
  payload: Record<string, any>;
  created_at: string;
}

// --- HELPER FUNCTIONS ---
const formatCurrency = (amount: number = 0) => `$${amount.toLocaleString()}`;
const formatNumber = (amount: number = 0) => amount.toLocaleString();
const formatTime = (timestamp: string) => {
  try {
    return formatInTimeZone(new Date(timestamp), Intl.DateTimeFormat().resolvedOptions().timeZone, "MMM d, h:mm a");
  } catch (e) {
    return "Invalid date";
  }
};
const getEventColor = (eventType: string) => {
  switch (eventType) {
    case 'new_listing': return 'bg-green-500/20 text-green-300 border-green-500/30';
    case 'price_change': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
    case 'sold_listing': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
    default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
  }
};
const getEventLabel = (eventType: string) => eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

// --- SUB-COMPONENTS ---

const Stat: FC<{ label: string; value: string | number }> = ({ label, value }) => (
  <div className="flex items-center gap-2">
    <span className="text-brand-text-muted">{label}</span>
    <span className="font-semibold text-brand-text-main">{value}</span>
  </div>
);

const MarketEventCard: FC<{ event: MarketEvent; onPhotoClick: (photos: string[]) => void; onViewDetails: (event: MarketEvent) => void; }> = ({ event, onPhotoClick, onViewDetails }) => {
  const { payload } = event;
  const photos = useMemo(() => payload.Media?.filter((m: any) => m.MediaCategory === 'Photo').map((m: any) => m.MediaURL) || [], [payload.Media]);
  const mainPhoto = photos.length > 0 ? photos[0] : null;

  // CORRECTED: Use correct data keys for beds, baths, and sqft
  const beds = payload.BedroomsTotal || payload.BedsTotal;
  const baths = payload.BathroomsTotalInteger || payload.BathsTotal;
  const sqft = payload.LivingArea || payload.BuildingAreaTotal || payload.AboveGradeFinishedArea;

  return (
    <div className="bg-brand-dark-blue-light border border-white/10 rounded-xl overflow-hidden shadow-lg flex flex-col">
      {mainPhoto && (
        <div 
          className="relative h-52 bg-cover bg-center cursor-pointer group"
          style={{ backgroundImage: `url(${mainPhoto})` }}
          onClick={() => photos.length > 0 && onPhotoClick(photos)}
        >
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <p className="text-white font-semibold">View Photos</p>
          </div>
          <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-sm px-2 py-1 rounded-md text-xs text-white flex items-center gap-1.5">
            <ImageIcon className="w-3 h-3" /> {photos.length}
          </div>
        </div>
      )}
      <div className="p-5 flex-grow flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getEventColor(event.event_type)}`}>{getEventLabel(event.event_type)}</span>
          <span className="text-xs text-brand-text-muted">{formatTime(event.created_at)}</span>
        </div>
        <h3 className="font-bold text-lg text-brand-text-main truncate" title={payload.UnparsedAddress}>{payload.UnparsedAddress || 'Unknown Address'}</h3>
        <p className="text-sm text-brand-text-muted mb-4">{payload.City}, {payload.StateOrProvince}</p>
        
        {/* UPDATED: 4-column grid for key stats */}
        <div className="grid grid-cols-4 gap-2 text-center my-4">
          <div><p className="text-xs text-brand-text-muted">Price</p><p className="font-semibold text-brand-text-main text-sm">{formatCurrency(payload.ListPrice)}</p></div>
          <div><p className="text-xs text-brand-text-muted">Beds</p><p className="font-semibold text-brand-text-main text-sm">{beds || '–'}</p></div>
          <div><p className="text-xs text-brand-text-muted">Baths</p><p className="font-semibold text-brand-text-main text-sm">{baths || '–'}</p></div>
          <div><p className="text-xs text-brand-text-muted">Sq. Ft.</p><p className="font-semibold text-brand-text-main text-sm">{sqft ? formatNumber(sqft) : '–'}</p></div>
        </div>
        
        <div className="flex-grow" />

        <button 
          onClick={() => onViewDetails(event)}
          className="w-full mt-4 px-4 py-2 bg-brand-accent/10 text-brand-accent font-semibold rounded-lg hover:bg-brand-accent/20 transition-colors"
        >
          View Details
        </button>
      </div>
    </div>
  );
};

const PhotoGalleryModal: FC<{ photos: string[]; onClose: () => void }> = ({ photos, onClose }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const next = () => setCurrentIndex(prev => (prev + 1) % photos.length);
  const prev = () => setCurrentIndex(prev => (prev - 1 + photos.length) % photos.length);
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') next(); if (e.key === 'ArrowLeft') prev(); if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
  return (
    <div className="fixed inset-0 bg-black/90 z-50 flex flex-col items-center justify-center" onClick={onClose}>
      <button className="absolute top-4 right-4 text-white/70 hover:text-white" onClick={onClose}><X size={32} /></button>
      <div className="relative w-full h-full max-w-6xl max-h-[85vh] flex items-center justify-center" onClick={e => e.stopPropagation()}>
        <button className="absolute left-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-3 bg-white/10 rounded-full" onClick={prev}><ChevronLeft size={24} /></button>
        <img src={photos[currentIndex]} alt={`Property photo ${currentIndex + 1}`} className="max-h-full max-w-full object-contain rounded-lg"/>
        <button className="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-3 bg-white/10 rounded-full" onClick={next}><ChevronRight size={24} /></button>
        <div className="absolute bottom-4 bg-black/60 text-white px-4 py-1.5 rounded-full text-sm">{currentIndex + 1} / {photos.length}</div>
      </div>
    </div>
  );
};

/**
 * NEW: Replaced Modal with Side Drawer for better UX
 */
const PropertyDetailDrawer: FC<{ event: MarketEvent | null; onClose: () => void }> = ({ event, onClose }) => {
  const payload = event?.payload;
  
  const detailItems = [
    { icon: DollarSign, label: 'Price', value: payload?.ListPrice ? formatCurrency(payload.ListPrice) : 'N/A' },
    { icon: BedDouble, label: 'Bedrooms', value: payload?.BedroomsTotal || payload?.BedsTotal },
    { icon: Bath, label: 'Bathrooms', value: payload?.BathroomsTotalInteger || payload?.BathsTotal },
    { icon: Square, label: 'Sq. Ft.', value: payload?.LivingArea ? formatNumber(payload.LivingArea) : null },
    { icon: Calendar, label: 'Year Built', value: payload?.YearBuilt },
  ].filter(item => item.value);

  return (
    <>
      {/* Overlay */}
      <div 
        className={`fixed inset-0 bg-black/70 z-30 transition-opacity duration-300 ${event ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />
      {/* Drawer */}
      <div className={`fixed top-0 right-0 h-full w-full max-w-2xl bg-brand-dark-blue border-l border-white/10 shadow-2xl z-40 transform transition-transform duration-300 ease-in-out ${event ? 'translate-x-0' : 'translate-x-full'}`}>
        {payload && (
          <div className="flex flex-col h-full">
            <header className="p-6 border-b border-white/10 flex justify-between items-start">
              <div>
                <h2 className="font-bold text-2xl text-brand-text-main">{payload.UnparsedAddress}</h2>
                <p className="text-md text-brand-text-muted">{payload.City}, {payload.StateOrProvince}</p>
              </div>
              <button onClick={onClose} className="p-2 rounded-full hover:bg-white/10"><X size={20} /></button>
            </header>

            <div className="p-6 overflow-y-auto flex-grow">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-8">
                {detailItems.map(item => (
                  <div key={item.label}>
                    <div className="text-sm text-brand-text-muted flex items-center gap-2 mb-1"><item.icon className="w-4 h-4" /> {item.label}</div>
                    <p className="font-semibold text-brand-text-main text-lg">{item.value}</p>
                  </div>
                ))}
              </div>

              <h3 className="font-semibold text-brand-text-main mb-3 text-xl">Description</h3>
              <p className="text-brand-text-muted leading-relaxed whitespace-pre-wrap mb-8 text-md">
                {payload.PublicRemarks || "No description provided."}
              </p>
            </div>
            
            {payload.ListingURL && (
              <footer className="p-6 border-t border-white/10 mt-auto">
                <a href={payload.ListingURL} target="_blank" rel="noopener noreferrer" className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-brand-accent text-brand-dark font-semibold rounded-lg hover:brightness-110 transition-transform hover:scale-105">
                  <LinkIcon size={16} /> View Original Listing
                </a>
              </footer>
            )}
          </div>
        )}
      </div>
    </>
  );
};

// --- MAIN PAGE COMPONENT ---
export default function MarketActivityPage() {
  const { api, user } = useAppContext();
  const router = useRouter();
  
  const [marketEvents, setMarketEvents] = useState<MarketEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  const [galleryPhotos, setGalleryPhotos] = useState<string[] | null>(null);
  const [detailedEvent, setDetailedEvent] = useState<MarketEvent | null>(null);

  const [eventTypeFilter, setEventTypeFilter] = useState('all');
  const [priceFilter, setPriceFilter] = useState('all');

  useEffect(() => { 
    if (user && user.user_type !== 'realtor' && !user.super_user) {
      router.push('/dashboard');
    }
  }, [user, router]);

  const fetchMarketActivity = async () => {
    try {
      setIsLoading(true); setError(null);
      const data: MarketEvent[] = await api.get('/api/market-activity?limit=1000');
      data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setMarketEvents(data);
      if(data.length > 0) setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch market activity:', err);
      setError('Failed to load market activity data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchMarketActivity(); }, [api]);

  const filteredEvents = useMemo(() => {
    return marketEvents.filter(event => {
      if (eventTypeFilter !== 'all' && event.event_type !== eventTypeFilter) return false;
      if (priceFilter !== 'all') {
        const price = event.payload?.ListPrice || 0;
        if (priceFilter === 'under_500k' && price >= 500000) return false;
        if (priceFilter === '500k_1m' && (price < 500000 || price >= 1000000)) return false;
        if (priceFilter === 'over_1m' && price < 1000000) return false;
      }
      return true;
    });
  }, [marketEvents, eventTypeFilter, priceFilter]);
  
  const clearFilters = () => { setEventTypeFilter('all'); setPriceFilter('all'); };

  if (!user || (user.user_type !== 'realtor' && !user.super_user)) return null;

  return (
    <>
      <main className="flex-1 p-6 sm:p-8 overflow-y-auto bg-brand-dark">
        <header className="mb-8">
          <h1 className="text-4xl sm:text-5xl font-bold text-brand-white tracking-tight">Live Market Activity</h1>
          <p className="text-brand-text-muted mt-2 text-lg">Real-time property events and opportunities.</p>
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
            <Stat label="Properties" value={filteredEvents.length} />
            <Stat label="Event Types" value={Array.from(new Set(filteredEvents.map(e => e.event_type))).length} />
            {lastUpdated && <Stat label="Last Updated" value={formatTime(lastUpdated.toISOString())} />}
          </div>
        </header>

        <div className="mb-8 p-4 bg-brand-dark-blue-light border border-white/10 rounded-xl flex flex-wrap items-center gap-4">
          <Filter className="w-5 h-5 text-brand-accent" />
          <h3 className="font-semibold text-brand-text-main mr-4">Filters</h3>
          <select value={eventTypeFilter} onChange={e => setEventTypeFilter(e.target.value)} className="bg-brand-dark border border-white/10 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent">
            <option value="all">All Event Types</option><option value="new_listing">New Listings</option><option value="price_change">Price Changes</option><option value="sold_listing">Sold</option>
          </select>
          <select value={priceFilter} onChange={e => setPriceFilter(e.target.value)} className="bg-brand-dark border border-white/10 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent">
            <option value="all">All Prices</option><option value="under_500k">Under $500k</option><option value="500k_1m">$500k - $1M</option><option value="over_1m">Over $1M</option>
          </select>
          <button onClick={clearFilters} className="ml-auto text-sm text-brand-text-muted hover:text-brand-accent transition-colors flex items-center gap-1.5"><X size={14}/> Clear</button>
        </div>

        {isLoading ? (
          <div className="text-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-accent mx-auto"></div></div>
        ) : error ? (
          <div className="text-center py-20"><p className="text-red-400">{error}</p></div>
        ) : filteredEvents.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6">
            {filteredEvents.map(event => (
              <MarketEventCard key={event.id} event={event} onPhotoClick={setGalleryPhotos} onViewDetails={setDetailedEvent} />
            ))}
          </div>
        ) : (
          <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
            <h3 className="text-lg font-semibold text-brand-text-main">No Market Activity</h3>
            <p className="text-brand-text-muted mt-1">Try adjusting your filters or check back later.</p>
          </div>
        )}
      </main>

      {galleryPhotos && <PhotoGalleryModal photos={galleryPhotos} onClose={() => setGalleryPhotos(null)} />}
      <PropertyDetailDrawer event={detailedEvent} onClose={() => setDetailedEvent(null)} />
    </>
  );
}