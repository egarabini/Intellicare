import { useState } from 'react';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Mail,
  Phone,
  Send,
  CheckCircle2,
  Clock,
  MessageSquare,
  User,
  HelpCircle,
  FileText,
  Handshake,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const contactSchema = z.object({
  nome: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  email: z.string().email('E-mail inválido'),
  telefone: z.string().optional(),
  assunto: z.string().min(1, 'Selecione um assunto'),
  mensagem: z.string().min(20, 'Mensagem deve ter no mínimo 20 caracteres'),
});

type ContactFormData = z.infer<typeof contactSchema>;

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 },
};

const assuntos = [
  { value: 'duvida', label: 'Dúvidas sobre o INTELLICARE', icon: HelpCircle },
  { value: 'suporte', label: 'Suporte Técnico', icon: MessageSquare },
  { value: 'parceria', label: 'Proposta de Parceria', icon: Handshake },
  { value: 'imprensa', label: 'Imprensa e Mídia', icon: FileText },
  { value: 'outro', label: 'Outro Assunto', icon: MessageSquare },
];

const canaisAtendimento = [
  {
    icon: Mail,
    title: 'E-mail',
    value: 'contato@intellicare.org.br',
    description: 'Respondemos em até 24 horas',
  },
  {
    icon: Phone,
    title: 'Telefone',
    value: '0800 123 4567',
    description: 'Segunda a sexta, 8h às 18h',
  },
  {
    icon: Clock,
    title: 'Horário de Atendimento',
    value: '24/7',
    description: 'Suporte técnico online',
  },
];

export default function ContatoPage() {
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    reset,
  } = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
  });

  const onSubmit = (data: ContactFormData) => {
    console.log('Contato:', data);
    setSubmitted(true);
  };

  const handleReset = () => {
    setSubmitted(false);
    reset();
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 py-16">
        <div className="container mx-auto px-4 max-w-2xl">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="text-center">
              <CardContent className="pt-12 pb-12">
                <CheckCircle2 className="h-20 w-20 text-green-500 mx-auto mb-6" />
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Mensagem Enviada!</h2>
                <p className="text-lg text-gray-600 mb-6">
                  Obrigado por entrar em contato. Recebemos sua mensagem e responderemos em breve.
                </p>
                <Button onClick={handleReset} size="lg">
                  Enviar Nova Mensagem
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 py-16">
        <div className="container mx-auto px-4">
          <motion.div {...fadeInUp}>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">Entre em Contato</h1>
            <p className="text-xl text-white/90 max-w-3xl">
              Estamos aqui para ajudar. Envie sua mensagem e responderemos o mais breve possível.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <motion.div {...fadeInUp} className="lg:col-span-2">
            <Card>
              <CardContent className="p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Envie sua Mensagem</h2>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="nome">
                        <User className="h-4 w-4 inline mr-1" />
                        Nome Completo
                      </Label>
                      <Input
                        id="nome"
                        {...register('nome')}
                        placeholder="Seu nome completo"
                      />
                      {errors.nome && (
                        <p className="text-sm text-red-500">{errors.nome.message}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="email">
                        <Mail className="h-4 w-4 inline mr-1" />
                        E-mail
                      </Label>
                      <Input
                        id="email"
                        type="email"
                        {...register('email')}
                        placeholder="seu@email.com"
                      />
                      {errors.email && (
                        <p className="text-sm text-red-500">{errors.email.message}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="telefone">
                        <Phone className="h-4 w-4 inline mr-1" />
                        Telefone (Opcional)
                      </Label>
                      <Input
                        id="telefone"
                        {...register('telefone')}
                        placeholder="(00) 00000-0000"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="assunto">Assunto</Label>
                      <Select onValueChange={(value) => setValue('assunto', value)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione o assunto" />
                        </SelectTrigger>
                        <SelectContent>
                          {assuntos.map((assunto) => (
                            <SelectItem key={assunto.value} value={assunto.value}>
                              <div className="flex items-center gap-2">
                                <assunto.icon className="h-4 w-4" />
                                {assunto.label}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {errors.assunto && (
                        <p className="text-sm text-red-500">{errors.assunto.message}</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="mensagem">
                      <MessageSquare className="h-4 w-4 inline mr-1" />
                      Mensagem
                    </Label>
                    <Textarea
                      id="mensagem"
                      {...register('mensagem')}
                      placeholder="Escreva sua mensagem aqui..."
                      rows={6}
                    />
                    {errors.mensagem && (
                      <p className="text-sm text-red-500">{errors.mensagem.message}</p>
                    )}
                  </div>

                  <Button type="submit" size="lg" className="w-full md:w-auto">
                    <Send className="h-4 w-4 mr-2" />
                    Enviar Mensagem
                  </Button>
                </form>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div {...fadeInUp} transition={{ delay: 0.1 }} className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Canais de Atendimento</h2>

            {canaisAtendimento.map((canal, index) => (
              <Card key={index}>
                <CardContent className="p-6 flex items-start gap-4">
                  <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <canal.icon className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900">{canal.title}</h3>
                    <p className="text-primary-600 font-medium">{canal.value}</p>
                    <p className="text-sm text-gray-500">{canal.description}</p>
                  </div>
                </CardContent>
              </Card>
            ))}

            <Card className="bg-primary-50 border-primary-200">
              <CardContent className="p-6">
                <h3 className="font-bold text-primary-900 mb-2">Precisa de ajuda urgente?</h3>
                <p className="text-primary-700 text-sm mb-4">
                  Para questões técnicas urgentes, utilize nosso chat de suporte disponível 24 horas
                  para usuários cadastrados.
                </p>
                <Button variant="outline" className="w-full">
                  Acessar Central de Ajuda
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
