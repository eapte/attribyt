import { Users, Activity, ShoppingCart } from "lucide-react";

interface FlowStep {
  label: string;
  value: number | string;
  icon: typeof Users;
}

export default function BusinessFlow({
  totalRows,
  uniqueUsers,
  conversions,
}: {
  totalRows: number;
  uniqueUsers: number;
  conversions: number;
}) {
  const steps: FlowStep[] = [
    { label: "Synced Events", value: totalRows, icon: Activity },
    { label: "Unique Users", value: uniqueUsers, icon: Users },
    { label: "Conversions", value: conversions, icon: ShoppingCart },
  ];

  return (
    <div className="dashboard-panel">
      <h3 className="panel-title">Business Flow</h3>
      <p className="hint" style={{ marginTop: -10, marginBottom: 16 }}>
        From synced data to conversions
      </p>
      <div className="flow-row">
        {steps.map((step, i) => {
          const Icon = step.icon;
          return (
            <div key={step.label} className="flow-step-wrap">
              <div className="flow-step">
                <div className="flow-step-icon">
                  <Icon size={16} strokeWidth={1.8} />
                </div>
                <div>
                  <div className="flow-step-value">{step.value}</div>
                  <div className="flow-step-label">{step.label}</div>
                </div>
              </div>
              {i < steps.length - 1 && <div className="flow-arrow">→</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
} 