import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Send, ExternalLink, CheckCircle, Clock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  LineChart, 
  Line, 
  ResponsiveContainer,
  Cell
} from 'recharts';

interface WorkflowStep {
  id: string;
  label: string;
  status: 'pending' | 'in_progress' | 'completed';
}

interface ActionButton {
  label: string;
  href?: string;
  onClick?: () => void;
  variant?: 'default' | 'outline';
  icon?: React.ReactNode;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  chart?: React.ReactNode;
  workflow?: WorkflowStep[];
  actions?: ActionButton[];
}

// Dynamic chart data - would be fetched from API in real implementation
const getChartData = () => ({
  distribution: [
    { name: 'Pick Up Cup', value: 45, color: '#000000' },
    { name: 'Pick Up Spoon', value: 38, color: '#333333' },
    { name: 'Place Object', value: 52, color: '#666666' },
    { name: 'Release Grip', value: 35, color: '#999999' },
  ],
  trainingLoss: [
    { epoch: 1, loss: 0.95, accuracy: 0.65 },
    { epoch: 2, loss: 0.82, accuracy: 0.71 },
    { epoch: 3, loss: 0.74, accuracy: 0.78 },
    { epoch: 4, loss: 0.68, accuracy: 0.82 },
    { epoch: 5, loss: 0.61, accuracy: 0.85 },
    { epoch: 6, loss: 0.57, accuracy: 0.88 },
  ]
});

const SampleDistributionChart = () => {
  const chartData = getChartData();
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData.distribution}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="name"
          angle={-45}
          textAnchor="end"
          height={80}
          tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
          stroke="var(--border)"
        />
        <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }} stroke="var(--border)" />
        <Tooltip contentStyle={{ background: 'var(--background)', color: 'var(--foreground)', border: '1px solid var(--border)' }} />
        <Bar dataKey="value" radius={[2, 2, 0, 0]} fill="var(--foreground)" />
      </BarChart>
    </ResponsiveContainer>
  );
};

const TrainingLossLineChart = () => {
  const chartData = getChartData();
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData.trainingLoss}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="epoch" tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }} stroke="var(--border)" />
        <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }} stroke="var(--border)" />
        <Tooltip contentStyle={{ background: 'var(--background)', color: 'var(--foreground)', border: '1px solid var(--border)' }} />
        <Line
          type="monotone"
          dataKey="loss"
          stroke="var(--primary)"
          strokeWidth={2}
          dot={{ fill: 'var(--primary)', strokeWidth: 2, r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="accuracy"
          stroke="var(--foreground)"
          strokeWidth={2}
          dot={{ fill: 'var(--foreground)', strokeWidth: 2, r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

const aiResponses = [
  {
    trigger: ['create behavior', 'new behavior', 'add behavior'],
    response: "I'll help you create a new behavior. Let me walk through the process:",
    workflow: [
      { id: '1', label: 'Analyzing linked data sources', status: 'completed' as const },
      { id: '2', label: 'Creating behavior "Precise Grasp"', status: 'completed' as const },
      { id: '3', label: 'Scanning available videos from data sources', status: 'completed' as const },
      { id: '4', label: 'Ready for video selection', status: 'completed' as const }
    ],
    actions: [
      {
        label: 'Select Videos for Concept',
        href: '/projects/demo-project/concepts',
        variant: 'default' as const,
        icon: <ArrowRight className="h-4 w-4" />
      },
      {
        label: 'View Data Sources',
        href: '/data-sources',
        variant: 'outline' as const,
        icon: <ExternalLink className="h-4 w-4" />
      }
    ]
  },
  {
    trigger: ['upload data', 'data source', 'add videos', 'upload videos'],
    response: "I'll help you set up a new data source for your video files:",
    workflow: [
      { id: '1', label: 'Creating folder "robot_arm_demos"', status: 'completed' as const },
      { id: '2', label: 'Setting up upload endpoint', status: 'completed' as const },
      { id: '3', label: 'Configuring metadata extraction', status: 'completed' as const },
      { id: '4', label: 'Ready for file uploads', status: 'completed' as const }
    ],
    actions: [
      {
        label: 'View Data Sources',
        href: '/data-sources',
        variant: 'default' as const,
        icon: <ArrowRight className="h-4 w-4" />
      },
      {
        label: 'Upload Files',
        href: '/data-sources/robot_arm_demos',
        variant: 'outline' as const,
        icon: <ExternalLink className="h-4 w-4" />
      }
    ]
  },
  {
    trigger: ['link data', 'connect project', 'attach data source'],
    response: "I'll help you link data sources to your project:",
    workflow: [
      { id: '1', label: 'Scanning available data sources', status: 'completed' as const },
      { id: '2', label: 'Linking "robot_arm_samples" as training data', status: 'completed' as const },
      { id: '3', label: 'Linking "grasping_testset" as test data', status: 'completed' as const },
      { id: '4', label: 'Project data pipeline configured', status: 'completed' as const }
    ],
    actions: [
      {
        label: 'Select Videos for Concepts',
        href: '/projects/demo-project/concepts',
        variant: 'default' as const,
        icon: <ArrowRight className="h-4 w-4" />
      },
      {
        label: 'Manage Data Sources',
        href: '/data-sources',
        variant: 'outline' as const,
        icon: <ExternalLink className="h-4 w-4" />
      }
    ]
  },
  {
    trigger: ['distribution', 'balance', 'class'],
    response: "Here's a sample distribution across behaviors:",
    chart: <SampleDistributionChart />
  },
  {
    trigger: ['training', 'accuracy', 'loss', 'performance'],
    response: "Training accuracy and loss over time:",
    chart: <TrainingLossLineChart />
  },
  {
    trigger: ['confusion', 'matrix', 'overlap'],
    response: "This confusion matrix shows high overlap between 'Pick Up Cup' and 'Pick Up Spoon'. Consider merging or relabeling these behaviors for better classification accuracy."
  },
  {
    trigger: ['improve', 'suggest', 'recommendation'],
    response: "Based on your current data distribution, I recommend:\n\n• Collect 15-20 more samples for 'Release Grip' behavior\n• Consider splitting 'Place Object' into more specific actions\n• Review similar gestures between cup and spoon pickup"
  },
  {
    trigger: ['ready', 'train', 'sufficient'],
    response: "Your dataset shows good balance overall. You have sufficient samples to begin training with VJEPA2 embeddings. Expect initial accuracy around 85% based on current class separation."
  }
];

export function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'm1',
      role: 'user',
      content: 'I want to train a model to classify robot arm behavior.'
    },
    {
      id: 'm2',
      role: 'assistant',
      content:
        [
          'Great — let’s scope it so we pick the right training plan. Could you clarify:',
          '• Behaviors to classify (discrete labels)?',
          '• Data modality and source (RGB, depth, RGB‑D), resolution/FPS, camera viewpoint?',
          '• Labeling granularity (clip‑level vs frame‑level) and approximate samples per class?',
          '• Scene variation (objects/background/lighting) and any “negative/other” class?',
          '• Constraints (latency, on‑device vs server, privacy)?'
        ].join('\n')
    },
    {
      id: 'm3',
      role: 'user',
      content:
        [
          'Behaviors: pick, place, idle, error.',
          'Data: ~20 short RGB‑D clips per behavior (640×480, 15–30fps), clip‑level labels.',
          'Single overhead camera, indoor workspace, varied small objects.'
        ].join('\n')
    },
    {
      id: 'm4',
      role: 'assistant',
      content:
        [
          'Plan:',
          '1) Start with video classification using pretrained vision embeddings and a lightweight temporal head. Options:',
          '   • RGB baseline: extract per‑frame embeddings (e.g., CLIP/V-JEPA2) → temporal pooling → linear classifier.',
          '   • RGB‑D: early fuse depth as an extra channel or train a parallel depth encoder and late‑fuse scores.',
          '2) Dataset: split ~70/15/15 (train/val/test). Ensure class balance; add an "other" class if needed.',
          '3) Augmentations: color jitter (RGB), slight spatial jitter, time cropping; keep depth scaling consistent.',
          '4) Training: 10–20 epochs, monitor val accuracy and confusion. Target ≥85% with current variety.',
          '5) Next steps: upload/organize clips, define labels, kick off a training job.'
        ].join('\n'),
      actions: [
        { label: 'Link Data Sources', href: '/data-sources', variant: 'outline' },
        { label: 'Define Concepts', href: '/projects/demo-project/concepts' }
      ]
    }
  ]);
  const [input, setInput] = useState('');

    const getAIResponse = (userInput: string): { response: string; chart?: React.ReactNode; workflow?: WorkflowStep[]; actions?: ActionButton[] } => {
    const lowerInput = userInput.toLowerCase();
    
    for (const response of aiResponses) {
      if (response.trigger.some(trigger => lowerInput.includes(trigger))) {
        return {
          response: response.response,
          chart: response.chart,
          workflow: response.workflow,
          actions: response.actions
        };
      }
    }
    
    return { 
      response: "I can help you with training strategy, data analysis, and behavior classification insights. Try asking about:\n\n• Create behavior or add new behavior\n• Upload data or add videos to data sources\n• Link data sources to projects\n• Class distribution and balance\n• Training readiness assessment\n• Behavior improvement suggestions\n• Performance metrics analysis" 
    };
  };

    const handleSend = () => {
    if (!input.trim()) return;
    
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input
    };
    
    const { response, chart, workflow, actions } = getAIResponse(input);
    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: response,
      chart,
      workflow,
      actions
    };
    
    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setInput('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-background border-l border-border">
      {/* Header */}
      <div className="p-4 border-b border-border" style={{
        background: 'linear-gradient(180deg, rgba(18,24,38,1) 0%, rgba(17,24,39,1) 100%)'
      }}>
        <h3 className="font-medium text-foreground">AI Research Assistant</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Analyze training data • Suggest improvements • Interpret results
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 text-sm shadow-sm ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-accent text-foreground border border-border'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                
                {/* Workflow Steps */}
                {message.workflow && (
                  <div className="mt-3 space-y-2">
                    {message.workflow.map((step) => (
                      <div key={step.id} className="flex items-center space-x-2 text-xs">
                        {step.status === 'completed' && (
                          <CheckCircle className="h-3 w-3 text-green-600 dark:text-green-400" />
                        )}
                        {step.status === 'in_progress' && (
                          <Clock className="h-3 w-3 text-blue-600 dark:text-blue-400 animate-spin" />
                        )}
                        {step.status === 'pending' && (
                          <div className="h-3 w-3 rounded-full border border-border" />
                        )}
                        <span className="text-muted-foreground">
                          {step.label}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Chart */}
                {message.chart && (
                  <div className="mt-3 bg-background rounded border border-border p-2">
                    {message.chart}
                  </div>
                )}
                
                {/* Action Buttons */}
                {message.actions && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {message.actions.map((action, index) => (
                      action.href ? (
                        <Link
                          key={index}
                          to={action.href}
                          className={`inline-flex items-center space-x-1 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                            action.variant === 'outline'
                              ? 'border border-border bg-background text-foreground hover:bg-accent'
                              : 'bg-primary text-primary-foreground hover:bg-primary/90'
                          }`}
                        >
                          <span>{action.label}</span>
                          {action.icon}
                        </Link>
                      ) : (
                        <Button
                          key={index}
                          onClick={action.onClick}
                          variant={action.variant === 'outline' ? 'outline' : 'default'}
                          size="sm"
                          className="text-xs h-7"
                        >
                          <span>{action.label}</span>
                          {action.icon && <span className="ml-1">{action.icon}</span>}
                        </Button>
                      )
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border bg-background">
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Message"
            className="flex-1 text-sm"
          />
          <Button
            onClick={handleSend}
            size="sm"
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            disabled={!input.trim()}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}