import { Container, Title, Text, SimpleGrid, TextInput, Textarea, Button, Group, Stack } from '@mantine/core';

export function Contact() {
  return (
    <Container size="lg" py={80}>
      <Stack align="center" gap="xs" mb="xl">
        <Title order={2} ta="center">Fale Conosco</Title>
        <Text c="dimmed" ta="center" maw={600}>
          Tem alguma dúvida ou quer saber mais sobre como o IntelliCare pode transformar sua instituição? Entre em contato.
        </Text>
      </Stack>

      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing={50}>
        <div>
          <Title order={3} mb="xl">Informações de Contato</Title>
          <Stack>
            <Text><strong>Email:</strong> contato@intellicare.ia.br</Text>
            <Text><strong>Disponibilidade:</strong> Resposta em até 24h</Text>
          </Stack>
        </div>
        <div>
          <Title order={3} mb="xl">Envie uma Mensagem</Title>
          <form onSubmit={(e) => e.preventDefault()}>
            <Stack>
              <TextInput
                label="Nome"
                placeholder="Seu nome"
                required
              />
              <TextInput
                label="Email"
                placeholder="seu@email.com"
                required
                type="email"
              />
              <Textarea
                label="Mensagem"
                placeholder="Sua mensagem"
                required
                rows={6}
              />
              <Group justify="flex-end" mt="md">
                <Button type="submit" size="lg" color="intelliTeal">Enviar Mensagem</Button>
              </Group>
            </Stack>
          </form>
        </div>
      </SimpleGrid>
    </Container>
  );
}
