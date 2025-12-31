import React from 'react';

export const Textarea = ({ 
  id, 
  name, 
  value, 
  onChange, 
  placeholder = '',
  required = false,
  rows = 4,
  className = ''
}) => {
  return (
    <textarea
      id={id}
      name={name}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      required={required}
      rows={rows}
      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
    />
  );
};

