module.exports = {
    apps: [
      {
        name: 'flask-app', // Nome do aplicativo
        script: 'app.py', // Caminho para o arquivo principal do Flask
        interpreter: './venv/bin/python', // Caminho para o interpretador do Python dentro do venv
        watch: true, // Habilita o modo de observação para reiniciar o aplicativo em mudanças
        env: {
          FLASK_ENV: 'development', // Variável de ambiente para desenvolvimento
          FLASK_APP: 'app.py', // Nome do arquivo Flask
          // Adicione outras variáveis de ambiente aqui, se necessário
        },
        env_production: {
          FLASK_ENV: 'production', // Variável de ambiente para produção
          // Adicione outras variáveis de ambiente para produção aqui
        },
      },
    ],
  };
  