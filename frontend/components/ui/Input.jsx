import React from 'react';

export const Input = ({ 
  id, 
  name, 
  type = 'text', 
  value, 
  onChange, 
  placeholder = '',
  required = false,
  className = ''
}) => {
  return (
    <input
      id={id}
      name={name}
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      required={required}
      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
    />
  );
};

