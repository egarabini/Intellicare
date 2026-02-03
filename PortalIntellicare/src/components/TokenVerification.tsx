import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Loader2, RefreshCw, Mail, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { backendApi } from '@/services/backendApi';

interface TokenVerificationProps {
  protocol: string;
  email: string;
  onVerified: () => void;
}

export function TokenVerification({ protocol, email, onVerified }: TokenVerificationProps) {
  const [token, setToken] = useState(['', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (countdown > 0 && !success) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown, success]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    
    const newToken = [...token];
    newToken[index] = value.slice(0, 1);
    setToken(newToken);
    setError('');

    // Move to next input
    if (value && index < 4) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when complete
    if (index === 4 && value) {
      const fullToken = [...newToken.slice(0, 4), value].join('');
      if (fullToken.length === 5) {
        handleVerify(fullToken);
      }
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !token[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerify = async (fullToken?: string) => {
    const tokenToVerify = fullToken || token.join('');
    
    if (tokenToVerify.length !== 5) {
      setError('Digite os 5 dígitos do código');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await requestsApi.verifyToken(protocol, tokenToVerify);
      if (response.success) {
        setSuccess(true);
        onVerified();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Código inválido');
      setToken(['', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setIsResending(true);
    setError('');

    try {
      await requestsApi.resendToken(protocol);
      setCountdown(60);
      setToken(['', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Erro ao reenviar código');
    } finally {
      setIsResending(false);
    }
  };

  if (success) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-green-50 border border-green-200 rounded-lg p-8 text-center"
      >
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h3 className="text-xl font-semibold text-green-900 mb-2">
          Email Validado com Sucesso!
        </h3>
        <p className="text-green-700 mb-4">
          Sua solicitação <strong>{protocol}</strong> foi recebida e será analisada.
        </p>
        <p className="text-sm text-green-600">
          Você receberá atualizações por email sobre o andamento.
        </p>
        <Button 
          className="mt-6" 
          onClick={() => window.location.href = `/acompanhamento/${protocol}`}
        >
          Acompanhar Solicitação
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border rounded-lg p-8"
    >
      <div className="text-center mb-6">
        <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Mail className="w-6 h-6 text-primary-600" />
        </div>
        <h3 className="text-lg font-semibold text-neutral-900">
          Valide seu Email
        </h3>
        <p className="text-neutral-600 mt-2">
          Enviamos um código de 5 dígitos para:<br />
          <strong>{email}</strong>
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex justify-center gap-2 mb-6">
        {token.map((digit, index) => (
          <Input
            key={index}
            ref={(el) => { inputRefs.current[index] = el; }}
            type="text"
            inputMode="numeric"
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            className="w-12 h-14 text-center text-2xl font-bold"
            maxLength={1}
            disabled={isLoading}
          />
        ))}
      </div>

      <Button
        className="w-full"
        onClick={() => handleVerify()}
        disabled={isLoading || token.join('').length !== 5}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
            Validando...
          </>
        ) : (
          'Validar Código'
        )}
      </Button>

      <div className="mt-6 text-center">
        {countdown > 0 ? (
          <p className="text-sm text-neutral-500">
            Reenviar código em {countdown}s
          </p>
        ) : (
          <button
            onClick={handleResend}
            disabled={isResending}
            className="text-sm text-primary-600 hover:text-primary-700 flex items-center justify-center mx-auto disabled:opacity-50"
          >
            {isResending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-1" />
                Reenviando...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-1" />
                Reenviar código
              </>
            )}
          </button>
        )}
      </div>

      <p className="text-xs text-neutral-400 text-center mt-4">
        Protocolo: {protocol}
      </p>
    </motion.div>
  );
}
