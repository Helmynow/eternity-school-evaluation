import React from 'react';

export const Select = ({ 
  id, 
  name, 
  value, 
  onChange, 
  children,
  required = false,
  className = ''
}) => {
  return (
    <select
      id={id}
      name={name}
      value={value}
      onChange={onChange}
      required={required}
      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
    >
      {children}
    </select>
  );
};

