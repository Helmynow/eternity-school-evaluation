import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Input } from '../components/ui/Input';

const AssignmentForm = ({ cycleId, onSubmit }) => {
  const [formData, setFormData] = useState({
    rater_email: '',
    target_email: '',
    target_group: 'peers',
    rater_context: 'peer_review',
    weight: 1.0
  });
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPeople();
  }, []);

  const fetchPeople = async () => {
    try {
      const response = await fetch('/api/people');
      const data = await response.json();
      setPeople(data);
    } catch (error) {
      console.error('Error fetching people:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'weight' ? parseFloat(value) : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/assignments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          cycle_id: cycleId
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (onSubmit) {
          onSubmit(data);
        }
        // Reset form
        setFormData({
          rater_email: '',
          target_email: '',
          target_group: 'peers',
          rater_context: 'peer_review',
          weight: 1.0
        });
        alert('Assignment created successfully!');
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to create assignment'}`);
      }
    } catch (error) {
      console.error('Error creating assignment:', error);
      alert('Error creating assignment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Evaluation Assignment</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="rater_email" className="block text-sm font-medium mb-2">
              Rater (Who is evaluating)
            </label>
            <Select
              id="rater_email"
              name="rater_email"
              value={formData.rater_email}
              onChange={handleChange}
              required
            >
              <option value="">Select rater</option>
              {people.map((person) => (
                <option key={person.email} value={person.email}>
                  {person.full_name} ({person.role_title})
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label htmlFor="target_email" className="block text-sm font-medium mb-2">
              Target (Who is being evaluated)
            </label>
            <Select
              id="target_email"
              name="target_email"
              value={formData.target_email}
              onChange={handleChange}
              required
            >
              <option value="">Select target</option>
              {people.map((person) => (
                <option key={person.email} value={person.email}>
                  {person.full_name} ({person.role_title})
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label htmlFor="target_group" className="block text-sm font-medium mb-2">
              Target Group
            </label>
            <Select
              id="target_group"
              name="target_group"
              value={formData.target_group}
              onChange={handleChange}
            >
              <option value="peers">Peers</option>
              <option value="direct_reports">Direct Reports</option>
              <option value="managers">Managers</option>
              <option value="self">Self</option>
              <option value="other">Other</option>
            </Select>
          </div>

          <div>
            <label htmlFor="rater_context" className="block text-sm font-medium mb-2">
              Rater Context
            </label>
            <Select
              id="rater_context"
              name="rater_context"
              value={formData.rater_context}
              onChange={handleChange}
            >
              <option value="peer_review">Peer Review</option>
              <option value="manager_review">Manager Review</option>
              <option value="direct_report_review">Direct Report Review</option>
              <option value="self_review">Self Review</option>
              <option value="360_review">360 Review</option>
            </Select>
          </div>

          <div>
            <label htmlFor="weight" className="block text-sm font-medium mb-2">
              Weight
            </label>
            <Input
              id="weight"
              name="weight"
              type="number"
              step="0.1"
              min="0"
              max="2"
              value={formData.weight}
              onChange={handleChange}
            />
            <p className="text-xs text-gray-500 mt-1">
              Weight factor for this evaluation (default: 1.0)
            </p>
          </div>

          <Button
            type="submit"
            variant="primary"
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Assignment'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default AssignmentForm;

