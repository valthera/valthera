import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { AppShell, Group, Text, NavLink, Stack } from '@mantine/core';
import { IconApi, IconSettings, IconLogout } from '@tabler/icons-react';

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, signOut } = useAuth();
  const location = useLocation();

  const handleSignOut = async () => {
    await signOut();
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <AppShell
      navbar={{ width: 300, breakpoint: 'sm' }}
      header={{ height: 60 }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <img src="/logo.svg" alt="Valthera" className="h-14 w-14" />
          <Group>
            <Text size="sm" c="dimmed">{user?.email}</Text>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Stack h="100%" justify="space-between">
          {/* Top Navigation */}
          <div>                        
            <NavLink
              component={Link}
              to="/dashboard"
              label="Perception"
              leftSection={<IconApi size="1rem" />}
              active={isActive('/dashboard') || isActive('/dashboard/api-tokens')}
              mb="xs"
            />
          </div>

          {/* Bottom Navigation */}
          <Stack gap="xs">
            <NavLink
              component={Link}
              to="/dashboard/settings"
              label="Settings"
              leftSection={<IconSettings size="1rem" />}
              active={isActive('/dashboard/settings')}
            />
            <NavLink
              label="Sign out"
              leftSection={<IconLogout size="1rem" />}
              onClick={handleSignOut}
              style={{ cursor: 'pointer' }}
            />
          </Stack>
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>
        {children}
      </AppShell.Main>
    </AppShell>
  );
}