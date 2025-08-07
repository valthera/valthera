import type { ReactNode } from 'react'
import { AppShell, Group, Text, Avatar, Menu, UnstyledButton, Divider, Stack, Box, rem, Flex, Burger } from '@mantine/core'
import { IconChevronDown, IconUser, IconLogout, IconCreditCard, IconKey, IconPlus, IconCircle } from '@tabler/icons-react'
import { useDisclosure, useMediaQuery } from '@mantine/hooks'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

interface Concept {
  name: string
  active?: boolean
}

interface Observation {
  name: string
  active?: boolean
}

interface AltAppShellProps {
  children: ReactNode
  breadcrumbs?: ReactNode
  sidebarItems: { label: string; active?: boolean; onClick?: () => void }[]
  appName?: string
  asideContent?: ReactNode
  footerContent?: ReactNode
  concepts?: Concept[]
  currentConcept?: string
  onSelectConcept?: (name: string) => void
  onNewConcept?: () => void
  observations?: Observation[]
  currentObservation?: string
  onSelectObservation?: (name: string) => void
  onNewObservation?: () => void
  hideSidebar?: boolean
}

export function AltAppShell({
  children,
  breadcrumbs,
  sidebarItems,
  appName = 'Valthera',
  asideContent,
  footerContent,
  concepts = [],
  currentConcept = '',
  onSelectConcept,
  onNewConcept,
  observations = [],
  currentObservation = '',
  onSelectObservation,
  onNewObservation,
  hideSidebar = false,
}: AltAppShellProps) {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [opened, { toggle }] = useDisclosure()
  const isMobile = useMediaQuery('(max-width: 48em)') // Mantine 'sm' breakpoint
  const showSidebarAppName = !isMobile || opened
  const showHeaderAppName = isMobile && !opened

  return (
    <AppShell
      layout="alt"
      header={{ height: 60 }}
      footer={footerContent ? { height: 60 } : undefined}
      navbar={hideSidebar ? undefined : { width: 260, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      aside={asideContent ? { width: 300, breakpoint: 'md', collapsed: { desktop: false, mobile: true } } : undefined}
      padding="md"
      styles={{
        main: { background: '#232323', minHeight: '100vh' },
        navbar: { background: '#232323', borderRight: '1px solid #333', paddingTop: 0 },
        header: { background: '#232323', borderBottom: '1px solid #333', zIndex: 100 },
        aside: { background: '#232323', borderLeft: '1px solid #333' },
        footer: { background: '#232323', borderTop: '1px solid #333' },
      }}
    >
      <AppShell.Header>
        <Flex h="100%" align="center" px="md" justify="space-between">
          <Group gap="md" align="center">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            {showHeaderAppName && (
              <Text fw={700} size="xl" c="#fff" style={{ letterSpacing: '-1px' }}>{appName}</Text>
            )}
            {breadcrumbs && (
              <Box ml="md">{breadcrumbs}</Box>
            )}
          </Group>
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
        {showHeaderAppName && (
          <Box mx={20} style={{ borderBottom: '1px solid #333' }} />
        )}
      </AppShell.Header>
      {!hideSidebar && (
        <AppShell.Navbar p={0}>
          {/* Logo and App Name */}
          {showSidebarAppName && (
            <>
              <Box px={20} py={13}>
                <Group gap={10} align="center">
                  <IconCircle size={32} color="#fff" stroke={1.5} />
                  <Text fw={700} size="xl" c="#fff" style={{ letterSpacing: '-1px' }}>{appName}</Text>
                </Group>
              </Box>
              <Box style={{ borderBottom: '1px solid #333', width: '100%' }} />
            </>
          )}
          {/* Concepts section, left-aligned and only once */}
          <Box px={20} pt={24}>
            <Text
              c="#aaa"
              size="md"
              fw={500}
              style={{
                letterSpacing: '0.02em',
                textAlign: 'left',
                display: 'block',
                marginBottom: 8,
                marginTop: 0,
                padding: 0,
              }}
            >
              Concepts
            </Text>
            {/* Always show concepts list expanded */}
            <Stack gap={2} pl={32} mb={8}>
              {concepts?.map((c) => (
                <UnstyledButton
                  key={c.name}
                  onClick={() => onSelectConcept?.(c.name)}
                  style={{
                    color: c.name === currentConcept ? '#fff' : '#bbb',
                    fontWeight: c.name === currentConcept ? 600 : 400,
                    borderRadius: rem(8),
                    padding: rem(8),
                    textAlign: 'left',
                    width: '100%',
                    fontSize: rem(15),
                    marginBottom: rem(2),
                    background: c.name === currentConcept ? 'rgba(79,209,197,0.08)' : 'transparent',
                    transition: 'background 0.2s',
                  }}
                >
                  {c.name}
                </UnstyledButton>
              ))}
              <UnstyledButton
                onClick={onNewConcept}
                style={{
                  color: '#4fd1c5',
                  fontWeight: 500,
                  borderRadius: rem(8),
                  padding: rem(8),
                  textAlign: 'left',
                  width: '100%',
                  fontSize: rem(15),
                  marginTop: rem(4),
                  background: 'rgba(79,209,197,0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: rem(6),
                }}
              >
                <IconPlus size={16} /> New Concept
              </UnstyledButton>
            </Stack>
          </Box>
          <Box p={10} style={{ borderBottom: '1px solid #333', width: '100%' }} />
          {/* Observations section */}
          {observations && observations.length > 0 && (
            <>
              <Box px={20} pt={24}>
                <Text
                  c="#aaa"
                  size="md"
                  fw={500}
                  style={{
                    letterSpacing: '0.02em',
                    textAlign: 'left',
                    display: 'block',
                    marginBottom: 8,
                    marginTop: 0,
                    padding: 0,
                  }}
                >
                  Observations
                </Text>
                {/* Always show observations list expanded */}
                <Stack gap={2} pl={32} mb={8}>
                  {observations?.map((o) => (
                    <UnstyledButton
                      key={o.name}
                      onClick={() => onSelectObservation?.(o.name)}
                      style={{
                        color: o.name === currentObservation ? '#fff' : '#bbb',
                        fontWeight: o.name === currentObservation ? 600 : 400,
                        borderRadius: rem(8),
                        padding: rem(8),
                        textAlign: 'left',
                        width: '100%',
                        fontSize: rem(15),
                        marginBottom: rem(2),
                        background: o.name === currentObservation ? 'rgba(79,209,197,0.08)' : 'transparent',
                        transition: 'background 0.2s',
                      }}
                    >
                      {o.name}
                    </UnstyledButton>
                  ))}
                  <UnstyledButton
                    onClick={onNewObservation}
                    style={{
                      color: '#4fd1c5',
                      fontWeight: 500,
                      borderRadius: rem(8),
                      padding: rem(8),
                      textAlign: 'left',
                      width: '100%',
                      fontSize: rem(15),
                      marginTop: rem(4),
                      background: 'rgba(79,209,197,0.08)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: rem(6),
                    }}
                  >
                    <IconPlus size={16} /> New Observation
                  </UnstyledButton>
                </Stack>
              </Box>
              <Box p={10} style={{ borderBottom: '1px solid #333', width: '100%' }} />
            </>
          )}
          {/* Other sidebar items */}
          <Stack gap="xs" p="md">
            {sidebarItems?.map((item) => (
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
                  textAlign: 'left',
                }}
              >
                {item.label}
              </UnstyledButton>
            ))}
          </Stack>        
          {/* Bottom section - aligned to bottom */}
          <Box style={{ marginTop: 'auto', padding: '20px', borderTop: '1px solid #333' }}>
            <Stack gap="xs">
              <UnstyledButton
                onClick={() => navigate('/upload')}
                style={{
                  color: '#bbb',
                  borderRadius: rem(8),
                  padding: rem(10),
                  fontWeight: 400,
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                  textAlign: 'left',
                  width: '100%',
                }}
              >
                Upload Video
              </UnstyledButton>
              <UnstyledButton
                style={{
                  color: '#bbb',
                  borderRadius: rem(8),
                  padding: rem(10),
                  fontWeight: 400,
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                  textAlign: 'left',
                  width: '100%',
                }}
              >
                Settings
              </UnstyledButton>
            </Stack>
          </Box>
        </AppShell.Navbar>
      )}
      {asideContent && <AppShell.Aside p="md">{asideContent}</AppShell.Aside>}
      <AppShell.Main>
        <Box maw={1200} ml={0} mr="auto" pt="md" px={20}>
          {children}
        </Box>
      </AppShell.Main>
      {footerContent && <AppShell.Footer p="md">{footerContent}</AppShell.Footer>}
    </AppShell>
  )
} 