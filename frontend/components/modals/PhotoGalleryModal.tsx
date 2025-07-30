'use client';

import { useState, useEffect, FC } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';

interface PhotoGalleryModalProps {
    photos: string[];
    onClose: () => void;
}

export const PhotoGalleryModal: FC<PhotoGalleryModalProps> = ({ photos, onClose }) => {
    const [currentIndex, setCurrentIndex] = useState(0);

    const next = () => setCurrentIndex(prev => (prev + 1) % photos.length);
    const prev = () => setCurrentIndex(prev => (prev - 1 + photos.length) % photos.length);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'ArrowRight') next();
            if (e.key === 'ArrowLeft') prev();
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onClose]);

    return (
        <div className="fixed inset-0 bg-black/90 z-50 flex flex-col items-center justify-center" onClick={onClose}>
            <button className="absolute top-4 right-4 text-white/70 hover:text-white" onClick={onClose}>
                <X size={32} />
            </button>
            <div className="relative w-full h-full max-w-6xl max-h-[85vh] flex items-center justify-center" onClick={e => e.stopPropagation()}>
                <button 
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-3 bg-white/10 rounded-full" 
                    onClick={prev}
                >
                    <ChevronLeft size={24} />
                </button>
                <img 
                    src={photos[currentIndex]} 
                    alt={`Photo ${currentIndex + 1}`} 
                    className="max-h-full max-w-full object-contain rounded-lg"
                />
                <button 
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-3 bg-white/10 rounded-full" 
                    onClick={next}
                >
                    <ChevronRight size={24} />
                </button>
                <div className="absolute bottom-4 bg-black/60 text-white px-4 py-1.5 rounded-full text-sm">
                    {currentIndex + 1} / {photos.length}
                </div>
            </div>
        </div>
    );
}; 