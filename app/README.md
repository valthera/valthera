# Blink - AWS Cognito Authentication App

A modern authentication system built with React, TypeScript, and AWS Cognito. Features secure user authentication with email verification, password reset, and protected routes. Now includes Stripe billing integration for payment method management.

## Features

- 🔐 **Secure Authentication** - Built on AWS Cognito's secure authentication system
- 💳 **Stripe Billing** - Complete payment method management with Stripe integration
- 🛡️ **Protected Routes** - Automatic route protection with redirects
- 📧 **Password Reset** - Secure password reset functionality with email verification
- ⚡ **Modern UI** - Beautiful, responsive design built with Tailwind CSS
- 📱 **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- 🔄 **Real-time Updates** - Automatic session management and state updates

## Tech Stack

- **Frontend**: React 19, TypeScript, Vite
- **Styling**: Tailwind CSS, Mantine UI
- **Authentication**: AWS Cognito (via Amplify)
- **Billing**: Stripe
- **Routing**: React Router DOM
- **State Management**: React Context API

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- pnpm (recommended) or npm
- AWS Account with Cognito setup

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd blink/app
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   ```

3. **Set up AWS Cognito**
   - Deploy the CDK stack to create Cognito resources
   - Get the User Pool ID, User Pool Client ID, and Identity Pool ID from CDK outputs

4. **Configure environment variables**
   ```bash
   cp env.example .env.local
   ```
   
   Edit `.env.local` and add your Cognito credentials:
   ```env
   VITE_COGNITO_USER_POOL_ID=us-east-1_your_user_pool_id
   VITE_COGNITO_USER_POOL_CLIENT_ID=your_user_pool_client_id
   VITE_COGNITO_IDENTITY_POOL_ID=us-east-1:your_identity_pool_id
   ```

5. **Start the development server**
   ```bash
   pnpm dev
   ```

6. **Open your browser**
   Navigate to `http://localhost:5173`

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── ProtectedRoute.tsx
│   └── PublicRoute.tsx
├── contexts/           # React contexts
│   └── AuthContext.tsx
├── lib/               # Utility libraries
│   └── cognito.ts
├── pages/             # Page components
│   ├── Dashboard.tsx
│   ├── ForgotPassword.tsx
│   ├── Landing.tsx
│   ├── SignIn.tsx
│   └── SignUp.tsx
├── App.tsx            # Main app component
└── main.tsx           # App entry point
```

## Authentication Flow

### Public Routes
- **Landing Page** (`/`) - Welcome page with sign up/sign in options
- **Sign In** (`/signin`) - User authentication form
- **Sign Up** (`/signup`) - User registration form with email confirmation
- **Forgot Password** (`/forgot-password`) - Password reset form with code verification

### Protected Routes
- **Dashboard** (`/dashboard`) - User dashboard (requires authentication)

### Route Protection
- **PublicRoute**: Redirects authenticated users to dashboard
- **ProtectedRoute**: Redirects unauthenticated users to sign in

## AWS Cognito Setup

### 1. Deploy CDK Stack
1. Navigate to the `cdk` directory
2. Install dependencies: `pip install -r requirements.txt`
3. Deploy the stack: `cdk deploy`
4. Note the outputs for User Pool ID, User Pool Client ID, and Identity Pool ID

### 2. Configure Authentication
The CDK stack automatically configures:
- User Pool with email-based authentication
- User Pool Client with OAuth flows
- Identity Pool for AWS resource access
- Password policies and account recovery settings

### 3. Email Configuration
1. Go to AWS Cognito Console
2. Navigate to your User Pool
3. Go to Messaging > Email configuration
4. Configure your email provider (SES recommended)

## Billing Features

### Payment Method Management
- **Add Payment Methods** - Securely add credit/debit cards using Stripe Elements
- **Update Payment Methods** - Edit cardholder names and billing details
- **Remove Payment Methods** - Safely remove payment methods
- **Default Payment Method** - Set and manage default payment methods

### Subscription Management
- **View Current Plan** - See your current subscription status
- **Upgrade/Downgrade** - Change your subscription plan
- **Billing History** - View past invoices and payments

## API Key Management

The application manages API keys through Cognito custom attributes:

1. **Automatic User Profile Creation**: When a user signs up, a profile is automatically created
2. **API Key Generation**: Users can generate API keys from the dashboard
3. **API Key Storage**: API keys are stored as custom attributes in Cognito
4. **API Key Regeneration**: Users can regenerate their API keys

## Installation

1. Install dependencies:
```bash
pnpm install
```

2. Start the development server:
```bash
pnpm dev
```

## Troubleshooting

### Cognito Configuration Issues
1. Check that your Cognito environment variables are correct
2. Verify that the User Pool Client is configured for your domain
3. Ensure email verification is enabled in your User Pool settings

### Authentication Issues
1. Check that your Cognito User Pool ID and Client ID are correct
2. Verify that email authentication is enabled in your Cognito settings
3. Make sure the callback URLs are configured properly

### API Key Issues
1. Ensure the user profile was created successfully
2. Check that the API key generation function is working
3. Verify that custom attributes are properly configured

## Features

- ✅ User authentication with AWS Cognito
- ✅ Email verification and confirmation
- ✅ Password reset with code verification
- ✅ API key generation and management
- ✅ User profile management
- ✅ Subscription management with Stripe
- ✅ Modern UI with Mantine and Tailwind CSS
- ✅ Responsive design

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_COGNITO_USER_POOL_ID` | Your AWS Cognito User Pool ID | Yes |
| `VITE_COGNITO_USER_POOL_CLIENT_ID` | Your AWS Cognito User Pool Client ID | Yes |
| `VITE_COGNITO_IDENTITY_POOL_ID` | Your AWS Cognito Identity Pool ID | Yes |

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm preview` - Preview production build
- `pnpm lint` - Run ESLint

## Deployment

### Vercel
1. Push your code to GitHub
2. Connect your repository to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy

### Netlify
1. Push your code to GitHub
2. Connect your repository to Netlify
3. Add environment variables in Netlify dashboard
4. Deploy

## Security Features

- **Email Verification**: Users must verify their email before accessing protected routes
- **Password Hashing**: Passwords are securely hashed by AWS Cognito
- **Session Management**: Automatic session handling and cleanup
- **Route Protection**: Unauthorized users are redirected to sign in
- **CSRF Protection**: Built-in CSRF protection via AWS Cognito

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

If you encounter any issues or have questions, please:

1. Check the [AWS Cognito documentation](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)
2. Search existing issues
3. Create a new issue with detailed information

## Acknowledgments

- [AWS Cognito](https://aws.amazon.com/cognito/) for the authentication backend
- [Tailwind CSS](https://tailwindcss.com) for the styling framework
- [React Router](https://reactrouter.com) for routing
- [Vite](https://vitejs.dev) for the build tool
