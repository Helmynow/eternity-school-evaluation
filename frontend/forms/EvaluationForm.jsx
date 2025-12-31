import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { Select } from '../components/ui/Select';

const EvaluationForm = ({ assignmentId, onSubmit }) => {
  const [formData, setFormData] = useState({
    rating: '',
    comments: '',
    status: 'draft'
  });
  const [loading, setLoading] = useState(false);
  const [assignment, setAssignment] = useState(null);

  useEffect(() => {
    if (assignmentId) {
      fetchAssignment();
    }
  }, [assignmentId]);

  const fetchAssignment = async () => {
    try {
      const response = await fetch(`/api/assignments/${assignmentId}`);
      const data = await response.json();
      setAssignment(data);
      
      // Load existing evaluation if any
      const evalResponse = await fetch(`/api/evaluations?assignment_id=${assignmentId}`);
      const evalData = await evalResponse.json();
      if (evalData.length > 0) {
        const existing = evalData[0];
        setFormData({
          rating: existing.rating || '',
          comments: existing.comments || '',
          status: existing.status
        });
      }
    } catch (error) {
      console.error('Error fetching assignment:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const method = assignment?.evaluation_id ? 'PUT' : 'POST';
      const url = assignment?.evaluation_id 
        ? `/api/evaluations/${assignment.evaluation_id}`
        : '/api/evaluations';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          assignment_id: assignmentId,
          ...formData,
          rating: parseFloat(formData.rating)
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (onSubmit) {
          onSubmit(data);
        }
        alert('Evaluation saved successfully!');
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to save evaluation'}`);
      }
    } catch (error) {
      console.error('Error submitting evaluation:', error);
      alert('Error submitting evaluation');
    } finally {
      setLoading(false);
    }
  };

  if (!assignment) {
    return <div>Loading assignment...</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Evaluation Form</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            Evaluating: <span className="font-semibold">{assignment.target_name || assignment.target_email}</span>
          </p>
          <p className="text-sm text-gray-600">
            Context: <span className="font-semibold">{assignment.rater_context}</span>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="rating" className="block text-sm font-medium mb-2">
              Rating (1-5)
            </label>
            <Select
              id="rating"
              name="rating"
              value={formData.rating}
              onChange={handleChange}
              required
            >
              <option value="">Select rating</option>
              <option value="1">1 - Needs Improvement</option>
              <option value="2">2 - Below Expectations</option>
              <option value="3">3 - Meets Expectations</option>
              <option value="4">4 - Exceeds Expectations</option>
              <option value="5">5 - Outstanding</option>
            </Select>
          </div>

          <div>
            <label htmlFor="comments" className="block text-sm font-medium mb-2">
              Comments
            </label>
            <Textarea
              id="comments"
              name="comments"
              value={formData.comments}
              onChange={handleChange}
              rows={6}
              placeholder="Provide detailed feedback..."
            />
          </div>

          <div>
            <label htmlFor="status" className="block text-sm font-medium mb-2">
              Status
            </label>
            <Select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
            >
              <option value="draft">Draft</option>
              <option value="submitted">Submit</option>
            </Select>
          </div>

          <div className="flex gap-2">
            <Button
              type="submit"
              variant="primary"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Evaluation'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setFormData({ rating: '', comments: '', status: 'draft' })}
            >
              Reset
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default EvaluationForm;

