import { FastifyInstance } from 'fastify';
import axios from 'axios';
import { z } from 'zod';

const CNES_API_URL = 'https://apidadosabertos.saude.gov.br/cnes';

// Schema para validação do CNES
const cnesValidationSchema = z.object({
  cnes: z.string().regex(/^\d{7}$/, 'CNES deve ter 7 dígitos numéricos')
});

// Schema para resposta do estabelecimento
const establishmentSchema = z.object({
  codigo_cnes: z.string(),
  numero_cnpj_entidade: z.string().optional(),
  nome_razao_social: z.string(),
  nome_fantasia: z.string().optional(),
  codigo_tipo_unidade: z.number(),
  descricao_tipo_unidade: z.string(),
  codigo_uf: z.number(),
  uf: z.string(),
  codigo_municipio: z.number(),
  descricao_municipio: z.string(),
  endereco_estabelecimento: z.string().optional(),
  numero_estabelecimento: z.string().optional(),
  bairro_estabelecimento: z.string().optional(),
  numero_telefone_estabelecimento: z.string().optional(),
  latitude_estabelecimento_decimo_grau: z.number().optional(),
  longitude_estabelecimento_decimo_grau: z.number().optional(),
  estabelecimento_possui_centro_cirurgico: z.number().optional(),
  estabelecimento_possui_centro_obstetrico: z.number().optional(),
  estabelecimento_possui_centro_neonatal: z.number().optional(),
  estabelecimento_possui_atendimento_hospitalar: z.number().optional(),
  estabelecimento_possui_servico_apoio: z.number().optional(),
  estabelecimento_possui_atendimento_ambulatorial: z.number().optional(),
});

export async function cnesRoutes(app: FastifyInstance) {
  // Validar CNES e retornar dados do estabelecimento
  app.get('/validate/:cnes', {
    schema: {
      description: 'Valida um código CNES e retorna dados do estabelecimento',
      tags: ['CNES'],
      params: {
        type: 'object',
        properties: {
          cnes: { type: 'string', description: 'Código CNES (7 dígitos)' }
        }
      },
      response: {
        200: {
          description: 'Dados do estabelecimento',
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'object',
              properties: {
                cnes: { type: 'string' },
                cnpj: { type: 'string' },
                razaoSocial: { type: 'string' },
                nomeFantasia: { type: 'string' },
                tipoUnidade: { type: 'string' },
                uf: { type: 'string' },
                municipio: { type: 'string' },
                endereco: { type: 'string' },
                telefone: { type: 'string' },
                latitude: { type: 'number' },
                longitude: { type: 'number' },
                recursos: {
                  type: 'object',
                  properties: {
                    centroCirurgico: { type: 'boolean' },
                    centroObstetrico: { type: 'boolean' },
                    centroNeonatal: { type: 'boolean' },
                    atendimentoHospitalar: { type: 'boolean' },
                    servicoApoio: { type: 'boolean' },
                    atendimentoAmbulatorial: { type: 'boolean' }
                  }
                }
              }
            }
          }
        },
        404: {
          description: 'Estabelecimento não encontrado',
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            error: { type: 'string' }
          }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { cnes } = cnesValidationSchema.parse(request.params);

      // Consulta API do Ministério da Saúde
      // Aumentamos o limit pois a API nem sempre respeita o filtro codigo_cnes
      const response = await axios.get(`${CNES_API_URL}/estabelecimentos`, {
        params: {
          codigo_cnes: cnes,
          limit: 100
        },
        timeout: 15000
      });

      // A API retorna { estabelecimentos: [...] } ou array direto
      const establishments = response.data?.estabelecimentos || response.data || [];

      if (!establishments || establishments.length === 0) {
        return reply.status(404).send({
          success: false,
          error: 'Estabelecimento não encontrado'
        });
      }

      // Filtra pelo CNES exato (a API nem sempre respeita o filtro)
      const establishment = establishments.find(
        (e: any) => String(e.codigo_cnes) === cnes || String(e.codigo_cnes).padStart(7, '0') === cnes
      );

      if (!establishment) {
        return reply.status(404).send({
          success: false,
          error: 'Estabelecimento não encontrado para o CNES informado'
        });
      }

      // Formata resposta
      return {
        success: true,
        data: {
          cnes: establishment.codigo_cnes,
          cnpj: establishment.numero_cnpj_entidade || null,
          razaoSocial: establishment.nome_razao_social,
          nomeFantasia: establishment.nome_fantasia || null,
          tipoUnidade: establishment.descricao_tipo_unidade,
          uf: establishment.uf,
          municipio: establishment.descricao_municipio,
          endereco: establishment.endereco_estabelecimento 
            ? `${establishment.endereco_estabelecimento}, ${establishment.numero_estabelecimento || 'S/N'} - ${establishment.bairro_estabelecimento || ''}`
            : null,
          telefone: establishment.numero_telefone_estabelecimento || null,
          latitude: establishment.latitude_estabelecimento_decimo_grau || null,
          longitude: establishment.longitude_estabelecimento_decimo_grau || null,
          recursos: {
            centroCirurgico: establishment.estabelecimento_possui_centro_cirurgico === 1,
            centroObstetrico: establishment.estabelecimento_possui_centro_obstetrico === 1,
            centroNeonatal: establishment.estabelecimento_possui_centro_neonatal === 1,
            atendimentoHospitalar: establishment.estabelecimento_possui_atendimento_hospitalar === 1,
            servicoApoio: establishment.estabelecimento_possui_servico_apoio === 1,
            atendimentoAmbulatorial: establishment.estabelecimento_possui_atendimento_ambulatorial === 1
          }
        }
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return reply.status(400).send({
          success: false,
          error: 'CNES inválido. Deve conter 7 dígitos numéricos.'
        });
      }

      request.log.error(error);
      return reply.status(500).send({
        success: false,
        error: 'Erro ao consultar CNES'
      });
    }
  });

  // Buscar estabelecimentos por filtros
  app.get('/establishments', {
    schema: {
      description: 'Busca estabelecimentos de saúde com filtros',
      tags: ['CNES'],
      querystring: {
        type: 'object',
        properties: {
          uf: { type: 'string', description: 'Código da UF (ex: 27 para Alagoas)' },
          municipio: { type: 'string', description: 'Código IBGE do município' },
          tipo: { type: 'string', description: 'Código do tipo de unidade' },
          status: { type: 'string', description: '1=Ativo, 0=Inativo' },
          limit: { type: 'string', default: '20', description: 'Itens por página (max 100)' },
          offset: { type: 'string', default: '0', description: 'Página (inicia em 0)' }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const query = request.query as Record<string, string>;
      
      const params: Record<string, string | number> = {};
      if (query.uf) params.codigo_uf = parseInt(query.uf);
      if (query.municipio) params.codigo_municipio = parseInt(query.municipio);
      if (query.tipo) params.codigo_tipo_unidade = parseInt(query.tipo);
      if (query.status) params.status = parseInt(query.status);
      params.limit = Math.min(parseInt(query.limit || '20'), 100);
      params.offset = parseInt(query.offset || '0');

      const response = await axios.get(`${CNES_API_URL}/estabelecimentos`, {
        params,
        timeout: 10000
      });

      return {
        success: true,
        data: response.data || [],
        pagination: {
          limit: params.limit,
          offset: params.offset,
          total: response.data?.length || 0
        }
      };
    } catch (error) {
      request.log.error(error);
      return reply.status(500).send({
        success: false,
        error: 'Erro ao buscar estabelecimentos'
      });
    }
  });

  // Listar tipos de unidades
  app.get('/unit-types', {
    schema: {
      description: 'Lista todos os tipos de unidades de saúde',
      tags: ['CNES']
    }
  }, async (request, reply) => {
    try {
      const response = await axios.get(`${CNES_API_URL}/tipounidades`, {
        timeout: 10000
      });

      return {
        success: true,
        data: response.data || []
      };
    } catch (error) {
      request.log.error(error);
      return reply.status(500).send({
        success: false,
        error: 'Erro ao buscar tipos de unidades'
      });
    }
  });
}
