FROM ubuntu

ARG USER=developer
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update \
  && apt install -y --no-install-recommends sudo git zsh curl wget ca-certificates \
  && apt clean \
  && apt autoremove -y \
  && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /usr/bin/zsh ${USER} \
  && echo "${USER} ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/${USER} \
  && chmod 0440 /etc/sudoers.d/${USER}

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -

RUN apt update && apt install -y less \
  git \
  procps \
  sudo \
  fzf \
  zsh \
  man-db \
  unzip \
  gnupg2 \
  gh \
  iptables \
  ipset \
  iproute2 \
  dnsutils \
  aggregate \
  jq \
  nodejs \
  nano

# Upgrade npm to the latest version
RUN npm install -g npm@latest

# Create workspace and config directories and set permissions
RUN mkdir -p /workspace /home/developer/.claude && \
  chown -R developer:developer /workspace /home/developer/.claude

# Install Claude
RUN npm install -g @anthropic-ai/claude-code

COPY init-firewall.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/init-firewall.sh && \
  echo "node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/node-firewall && \
  chmod 0440 /etc/sudoers.d/node-firewall

USER ${USER}
ARG HOME=/home/${USER}
ARG ZSH=${HOME}/.oh-my-zsh
ARG ZSH_CUSTOM=${ZSH}/custom
WORKDIR ${HOME}



RUN <<EOT
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
    mkdir -p ${ZSH_CUSTOM}
    git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM}/plugins/zsh-autosuggestions
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting
    sed -i.bak 's/plugins=(\(.*\))/plugins=(\1 zsh-autosuggestions zsh-syntax-highlighting)/' ~/.zshrc
EOT


ARG SPACESHIP_REMOTE=https://github.com/spaceship-prompt/spaceship-prompt.git
RUN <<EOT
    git clone ${SPACESHIP_REMOTE} ${ZSH_CUSTOM}/themes/spaceship-prompt --depth=1
    ln -s ${ZSH_CUSTOM}/themes/spaceship-prompt/spaceship.zsh-theme ${ZSH_CUSTOM}/themes/spaceship.zsh-theme
    sed -i 's|ZSH_THEME="robbyrussell"|ZSH_THEME="spaceship"|g' .zshrc
EOT


RUN <<EOT
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
    echo 'eval "$(uvx --generate-shell-completion zsh)"' >> ~/.zshrc
EOT

# Copy and set up firewall script
