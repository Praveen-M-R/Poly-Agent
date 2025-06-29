import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/HealthCheck.css';

const HealthCheckForm = ({ onSubmit, initialValues = {}, isEditing = false }) => {
  const defaultValues = {
    name: '',
    interval_days: 0,
    interval_hours: 0,
    interval_minutes: 5,
    grace_days: 0,
    grace_hours: 0,
    grace_minutes: 5,
    notify_email: '',
    notify_webhook: '',
    is_active: true,
    description: '',
    url: '',
    response_time_threshold: 1000,
    ...initialValues
  };

  const [formData, setFormData] = useState(defaultValues);
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
    
    // Clear error for this field when user edits it
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: ''
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    // Validate interval values are non-negative
    if (formData.interval_days < 0) {
      newErrors.interval_days = 'Days must be non-negative';
    }
    if (formData.interval_hours < 0) {
      newErrors.interval_hours = 'Hours must be non-negative';
    }
    if (formData.interval_minutes < 0) {
      newErrors.interval_minutes = 'Minutes must be non-negative';
    }
    
    // Validate grace period values are non-negative
    if (formData.grace_days < 0) {
      newErrors.grace_days = 'Days must be non-negative';
    }
    if (formData.grace_hours < 0) {
      newErrors.grace_hours = 'Hours must be non-negative';
    }
    if (formData.grace_minutes < 0) {
      newErrors.grace_minutes = 'Minutes must be non-negative';
    }
    
    // Validate at least one of the interval fields is greater than 0
    if (formData.interval_days === 0 && formData.interval_hours === 0 && formData.interval_minutes === 0) {
      newErrors.interval = 'At least one time interval (days, hours, or minutes) must be greater than 0';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isValidUrl = (string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      await onSubmit(formData);
    } catch (err) {
      // If onSubmit throws, we'll display the error 
      console.error('Error submitting form:', err);
      
      // Check if response contains validation errors
      if (err.message && err.message.includes(':')) {
        const errorParts = err.message.split(';');
        const newErrors = {};
        
        errorParts.forEach(part => {
          const [key, message] = part.split(':').map(s => s.trim());
          if (key && message) {
            newErrors[key] = message;
          }
        });
        
        setErrors(newErrors);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="health-check-form" onSubmit={handleSubmit}>
      {/* Basic Information Section */}
      <div className="form-section">
        <h3>Basic Information</h3>
        <div className="form-group">
          <label htmlFor="name">Name *</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={errors.name ? 'error' : ''}
            required
          />
          {errors.name && <div className="error-message">{errors.name}</div>}
          <small>A descriptive name for your health check</small>
        </div>
      </div>

      {/* Notification Settings Section */}
      <div className="form-section">
        <h3>Notification Settings</h3>
        <div className="form-group">
          <label htmlFor="notify_email">Email Notification</label>
          <input
            type="email"
            id="notify_email"
            name="notify_email"
            value={formData.notify_email}
            onChange={handleChange}
            placeholder="Email address for notifications"
          />
          <small>Email address to receive notifications when the check fails</small>
        </div>

        <div className="form-group">
          <label htmlFor="notify_webhook">Webhook URL</label>
          <input
            type="text"
            id="notify_webhook"
            name="notify_webhook"
            value={formData.notify_webhook}
            onChange={handleChange}
            placeholder="Webhook URL for notifications"
          />
          <small>Webhook URL to receive notifications when the check fails</small>
        </div>
        
        <div className="form-group">
          <label htmlFor="url">Target URL (Optional)</label>
          <input
            type="text"
            id="url"
            name="url"
            value={formData.url}
            onChange={handleChange}
            placeholder="URL to monitor (optional)"
          />
          <small>The URL to monitor (optional)</small>
        </div>
      </div>

      {/* Timing Settings Section */}
      <div className="form-section">
        <h3>Timing Settings</h3>
        
        {/* Duration */}
        <div className="form-group">
          <label>Interval</label>
          {errors.interval && <div className="error-message">{errors.interval}</div>}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="interval_days">Days</label>
              <input
                type="number"
                id="interval_days"
                name="interval_days"
                min="0"
                value={formData.interval_days}
                onChange={handleChange}
                className={errors.interval_days ? 'error' : ''}
              />
              {errors.interval_days && <div className="error-message">{errors.interval_days}</div>}
            </div>
            
            <div className="form-group">
              <label htmlFor="interval_hours">Hours</label>
              <input
                type="number"
                id="interval_hours"
                name="interval_hours"
                min="0"
                value={formData.interval_hours}
                onChange={handleChange}
                className={errors.interval_hours ? 'error' : ''}
              />
              {errors.interval_hours && <div className="error-message">{errors.interval_hours}</div>}
            </div>
            
            <div className="form-group">
              <label htmlFor="interval_minutes">Minutes</label>
              <input
                type="number"
                id="interval_minutes"
                name="interval_minutes"
                min="0"
                value={formData.interval_minutes}
                onChange={handleChange}
                className={errors.interval_minutes ? 'error' : ''}
              />
              {errors.interval_minutes && <div className="error-message">{errors.interval_minutes}</div>}
            </div>
          </div>
          <small>How often the service should ping the health check</small>
        </div>
        
        {/* Grace Period */}
        <div className="form-group">
          <label>Grace Period</label>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="grace_days">Days</label>
              <input
                type="number"
                id="grace_days"
                name="grace_days"
                min="0"
                value={formData.grace_days}
                onChange={handleChange}
                className={errors.grace_days ? 'error' : ''}
              />
              {errors.grace_days && <div className="error-message">{errors.grace_days}</div>}
            </div>
            
            <div className="form-group">
              <label htmlFor="grace_hours">Hours</label>
              <input
                type="number"
                id="grace_hours"
                name="grace_hours"
                min="0"
                value={formData.grace_hours}
                onChange={handleChange}
                className={errors.grace_hours ? 'error' : ''}
              />
              {errors.grace_hours && <div className="error-message">{errors.grace_hours}</div>}
            </div>
            
            <div className="form-group">
              <label htmlFor="grace_minutes">Minutes</label>
              <input
                type="number"
                id="grace_minutes"
                name="grace_minutes"
                min="0"
                value={formData.grace_minutes}
                onChange={handleChange}
                className={errors.grace_minutes ? 'error' : ''}
              />
              {errors.grace_minutes && <div className="error-message">{errors.grace_minutes}</div>}
            </div>
          </div>
          <small>Additional time to wait before alerting after a missed ping</small>
        </div>
      </div>
      
      <div className="form-actions">
        <button 
          type="submit" 
          className="btn btn-primary" 
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : isEditing ? 'Update Health Check' : 'Create Health Check'}
        </button>
      </div>
    </form>
  );
};

export default HealthCheckForm; 