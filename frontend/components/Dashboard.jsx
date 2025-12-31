import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';

const Dashboard = () => {
  const [cycles, setCycles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCycle, setSelectedCycle] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [biasReport, setBiasReport] = useState(null);

  useEffect(() => {
    fetchCycles();
  }, []);

  const fetchCycles = async () => {
    try {
      const response = await fetch('/api/cycles');
      const data = await response.json();
      setCycles(data);
      if (data.length > 0) {
        setSelectedCycle(data[0].id);
        loadCycleData(data[0].id);
      }
    } catch (error) {
      console.error('Error fetching cycles:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCycleData = async (cycleId) => {
    try {
      // Load weight matrix metrics
      const metricsResponse = await fetch(`/api/cycles/${cycleId}/weight_matrix`);
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData.metrics);

      // Load bias report
      const biasResponse = await fetch(`/api/cycles/${cycleId}/bias`);
      const biasData = await biasResponse.json();
      setBiasReport(biasData);
    } catch (error) {
      console.error('Error loading cycle data:', error);
    }
  };

  const handleCycleChange = (cycleId) => {
    setSelectedCycle(cycleId);
    loadCycleData(cycleId);
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Evaluation Dashboard</h1>
        <Button onClick={fetchCycles}>Refresh</Button>
      </div>

      {/* Cycle Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Select Cycle</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            {cycles.map((cycle) => (
              <Button
                key={cycle.id}
                variant={selectedCycle === cycle.id ? 'primary' : 'outline'}
                onClick={() => handleCycleChange(cycle.id)}
              >
                {cycle.code} - {cycle.name}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Rater Load Balance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Mean:</span>
                  <span className="font-bold">{metrics.rater_load_mean?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Std Dev:</span>
                  <span>{metrics.rater_load_std?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Coefficient of Variation:</span>
                  <Badge variant={metrics.rater_load_cv > 0.3 ? 'warning' : 'success'}>
                    {(metrics.rater_load_cv * 100).toFixed(1)}%
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Target Load Balance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Mean:</span>
                  <span className="font-bold">{metrics.target_load_mean?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Std Dev:</span>
                  <span>{metrics.target_load_std?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Coefficient of Variation:</span>
                  <Badge variant={metrics.target_load_cv > 0.3 ? 'warning' : 'success'}>
                    {(metrics.target_load_cv * 100).toFixed(1)}%
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Coverage</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <div className="text-4xl font-bold">
                  {(metrics.coverage * 100).toFixed(1)}%
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  of possible assignments
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Bias Report */}
      {biasReport && (
        <Card>
          <CardHeader>
            <CardTitle>Bias Detection Report</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {biasReport.role_bias?.status === 'analyzed' && (
                <div>
                  <h3 className="font-semibold mb-2">Role Bias</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(biasReport.role_bias.contexts || {}).map(([context, data]) => (
                      <div key={context} className="p-3 bg-gray-50 rounded">
                        <div className="text-sm font-medium">{context}</div>
                        <div className="text-lg font-bold">{data.mean?.toFixed(2)}</div>
                        <div className="text-xs text-gray-500">{data.count} evaluations</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {biasReport.harshness_bias?.status === 'analyzed' && (
                <div>
                  <h3 className="font-semibold mb-2">Harshness/Leniency Bias</h3>
                  <div className="space-y-2">
                    {Object.entries(biasReport.harshness_bias.rater_bias || {})
                      .slice(0, 5)
                      .map(([email, data]) => (
                        <div key={email} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="text-sm">{email}</span>
                          <Badge variant={data.bias < -0.5 ? 'danger' : data.bias > 0.5 ? 'success' : 'neutral'}>
                            {data.interpretation} ({data.bias > 0 ? '+' : ''}{data.bias.toFixed(2)})
                          </Badge>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;

