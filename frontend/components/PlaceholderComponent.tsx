// components/PlaceholderComponent.tsx
import React from 'react';

interface PlaceholderComponentProps {
  title: string;
  message: string;
}

const PlaceholderComponent: React.FC<PlaceholderComponentProps> = ({ title, message }) => {
  return (
    <div className="bg-brand-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-brand-primary">{title}</h3>
      <p className="text-sm text-gray-600">{message}</p>
    </div>
  );
};

export default PlaceholderComponent;
