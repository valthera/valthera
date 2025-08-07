import type { ReactNode } from 'react'
import { AppShell, Group, Text, Avatar, Menu, UnstyledButton, Divider, Stack, Box, rem, Flex } from '@mantine/core'
import { IconChevronDown, IconUser, IconLogout, IconKey } from '@tabler/icons-react'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

interface SidebarLayoutProps {
  children: ReactNode
  breadcrumbs?: ReactNode
  sidebarItems: { label: string; active?: boolean; onClick?: () => void }[]
  appName?: string
}

export function SidebarLayout({
  children,
  breadcrumbs,
  sidebarItems,
  appName = 'Valthera',
}: SidebarLayoutProps) {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  return (
    <AppShell
      padding="md"
      navbar={{ width: 260, breakpoint: 'sm' }}
      header={{ height: 56 }}
      styles={{
        main: { background: '#232323', minHeight: '100vh' },
        navbar: { background: '#232323', borderRight: '1px solid #333', paddingTop: 0 },
        header: { background: '#232323', borderBottom: '1px solid #333', zIndex: 100 },
      }}
    >
      <AppShell.Header>
        <Flex h="100%" align="center" px="md" justify="flex-end">
          {/* Right: Avatar menu only */}
          <Menu shadow="md" width={200} position="bottom-end">
            <Menu.Target>
              <UnstyledButton>
                <Group gap="xs">
                  <Avatar radius="xl" size={32} color="blue">
                    {user?.email?.[0]?.toUpperCase() || '?'}
                  </Avatar>
                  <IconChevronDown size={18} color="#bbb" />
                </Group>
              </UnstyledButton>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>Account</Menu.Label>
              <Menu.Item leftSection={<IconUser size={16} />} onClick={() => navigate('/account')}>Profile</Menu.Item>
              <Menu.Item leftSection={<IconKey size={16} />} onClick={() => navigate('/account#api')}>API Key</Menu.Item>
              <Divider />
              <Menu.Item color="red" leftSection={<IconLogout size={16} />} onClick={signOut}>Sign out</Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Flex>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <Text fw={700} size="xl" mb="lg" c="#fff" style={{ letterSpacing: '-1px' }}>{appName}</Text>
        <Stack gap="xs" mt="md">
          {sidebarItems.map((item) => (
            <UnstyledButton
              key={item.label}
              onClick={item.onClick}
              style={{
                background: item.active ? '#333' : 'transparent',
                color: item.active ? '#fff' : '#bbb',
                borderRadius: rem(8),
                padding: rem(10),
                fontWeight: item.active ? 600 : 400,
                cursor: 'pointer',
                transition: 'background 0.2s',
              }}
            >
              {item.label}
            </UnstyledButton>
          ))}
        </Stack>
      </AppShell.Navbar>
      <AppShell.Main>
        <Box maw={1200} mx="auto" pt="md">
          {/* Breadcrumbs at the top of main content */}
          {breadcrumbs && (
            <Box mb="lg">{breadcrumbs}</Box>
          )}
          {children}
        </Box>
      </AppShell.Main>
    </AppShell>
  )
} 