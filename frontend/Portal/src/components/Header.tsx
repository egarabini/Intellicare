
import {
  Container,
  Burger,
  Button,
  Drawer,
  ScrollArea,
  rem,
  Image,
  Box,
  Stack,
  Group,
} from '@mantine/core';
import { useDisclosure, useWindowScroll } from '@mantine/hooks';
import classes from './Header.module.css';

const NAV_LINKS = [
  { label: 'Plataforma', href: '#features' },
  { label: 'Agentes IA', href: '#agents' },
  { label: 'Sobre', href: '#about' },
  { label: 'Contato', href: '#contact' },
];

export function Header() {
  const [drawerOpened, { toggle: toggleDrawer, close: closeDrawer }] = useDisclosure(false);
  const [scroll] = useWindowScroll();

  const items = NAV_LINKS.map((link) => (
    <a
      key={link.label}
      href={link.href}
      className={classes.link}
      onClick={(event) => {
        event.preventDefault();
        const target = document.querySelector<HTMLElement>(event.currentTarget.getAttribute('href')!);
        if (target) {
            const headerOffset = 100; // Adjust as needed
            const elementPosition = target.offsetTop;
            const offsetPosition = elementPosition - headerOffset;
      
            window.scrollTo({
              top: offsetPosition,
              behavior: 'smooth',
            });
        }
        closeDrawer();
      }}
    >
      {link.label}
    </a>
  ));

  return (
    <Box>
      <header className={`${classes.header} ${scroll.y > 20 ? classes.scrolled : ''}`}>
        <Container size="xl" className={classes.inner}>
          <Image src="/logo/logo_completo_intellicare.png" h={35} alt="IntelliCare logo" />
          <Group gap={30} visibleFrom="sm">
            {items}
            <Button component="a" href="#contact" variant="filled" color="intelliTeal">
              Acessar Plataforma
            </Button>
          </Group>
          <Burger opened={drawerOpened} onClick={toggleDrawer} hiddenFrom="sm" />
        </Container>
      </header>

      <Drawer
        opened={drawerOpened}
        onClose={closeDrawer}
        size="100%"
        padding="md"
        title="Navegação"
        hiddenFrom="sm"
        zIndex={1000000}
      >
        <ScrollArea h={`calc(100vh - ${rem(80)})`} mx="-md">
          <Stack gap="xl" p="md">
            {items}
            <Button component="a" href="#contact" variant="filled" color="intelliTeal" fullWidth>
              Acessar Plataforma
            </Button>
          </Stack>
        </ScrollArea>
      </Drawer>
    </Box>
  );
}
