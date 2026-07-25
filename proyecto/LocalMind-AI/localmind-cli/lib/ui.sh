#!/bin/bash

# Setup Colors (Safe detection based on terminal capability)
setup_colors() {
    if [ -t 1 ] && [ "${TERM:-}" != "dumb" ]; then
        RED='\033[0;31m'
        GREEN='\033[0;32m'
        YELLOW='\033[1;33m'
        BLUE='\033[0;34m'
        CYAN='\033[0;36m'
        BOLD='\033[1m'
        DIM='\033[2m'
        NC='\033[0m'
    else
        RED='' GREEN='' YELLOW='' BLUE='' CYAN='' BOLD='' DIM='' NC=''
    fi
}

# Run color setup
setup_colors

# Logging Helpers (Matched with Gentle-AI style)
info()    { echo -e "${BLUE}[info]${NC}    $*"; }
success() { echo -e "${GREEN}[ok]${NC}      $*"; }
warn()    { echo -e "${YELLOW}[warn]${NC}    $*"; }
error()   { echo -e "${RED}[error]${NC}   $*" >&2; }
fatal()   { error "$@"; exit 1; }
step()    { echo -e "\n${CYAN}${BOLD}==>${NC} ${BOLD}$*${NC}"; }

# Print ASCII Art Banner
print_banner() {
    clear
    echo -e "${CYAN}${BOLD}"
    cat << 'EOF'
                             ▓▓▓▓▓▓▓▓▓                            
                           ▓▓▓▓▓▓ ▓▓▓▓▓▓▓                         
                        ▓▓▓▓▓         ▓▓▓▓▓                       
                       ▓▓▓▓             ▓▓▓▓                      
                     ▓▓▓▓                 ▓▓▓▓                    
                    ▓▓▓▓                   ▓▓▓▓                   
                   ▓▓▓▓                      ▓▓▓                  
                  ▓▓▓▓                        ▓▓▓                 
                 ▓▓▓▓          ▓▓▓▓▓          ▓▓▓▓                
                ▓▓▓▓        ▓▓▓▓▓▓▓▓▓▓▓        ▓▓▓▓               
                ▓▓▓       ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓       ▓▓▓▓              
               ▓▓▓      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      ▓▓▓▓             
              ▓▓▓▓     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓     ▓▓▓▓             
             ▓▓▓▓    ▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓    ▓▓▓▓            
            ▓▓▓▓    ▓▓▓▓▓▓▓   ▓▓▓▓▓▓▓▓   ▓▓▓▓▓▓     ▓▓▓           
           ▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓          
          ▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓         
          ▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓         
           ▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓          
            ▓▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓    ▓▓▓▓           
              ▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓             
                ▓▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓               
                  ▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓                 
                      ▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓                    
                           ▓▓ ▓▓▓▓▓▓▓ ▓▓▓                         
                              ▓▓▓▓▓▓▓                             
                             ▓▓▓   ▓▓▓                            
                             ▓▓▓   ▓▓▓                            
                              ▓▓▓▓▓▓▓                             
                                 ▓▓                               
EOF
    echo -e "${NC}"
    echo "=========================================================="
    echo -e "${BLUE}  Asistente Personal Multitarea Optimizado en Local ${NC}"
    echo "=========================================================="
    echo ""
}

# Yes/No Prompt (asks for confirmation, exits if required and rejected)
prompt_confirm() {
    local question=$1
    local required=$2 # "required" or "optional"
    local default=$3  # "Y" or "N"
    
    local prompt="[y/n]"
    if [ "$default" = "Y" ]; then
        prompt="[Y/n]"
    elif [ "$default" = "N" ]; then
        prompt="[y/N]"
    fi
    
    while true; do
        read -p "$(echo -e "${BOLD}$question $prompt: ${NC}")" yn
        
        # Handle default
        if [ -z "$yn" ]; then
            yn=$default
        fi
        
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) 
                if [ "$required" = "required" ]; then
                    fatal "Instalación cancelada: Se requería esta opción para continuar."
                fi
                return 1;;
            * ) echo "Por favor responde con 'y' (sí) o 'n' (no).";;
        esac
    done
}

# Select item from list
prompt_select() {
    local title=$1
    shift
    local options=("$@")
    
    echo -e "${BOLD}$title:${NC}"
    for i in "${!options[@]}"; do
        echo -e "  $((i+1)). ${options[$i]}"
    done
    
    while true; do
        read -p "$(echo -e "\n${BOLD}Selecciona una opción (1-${#options[@]}): ${NC}")" choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#options[@]}" ]; then
            return $((choice-1))
        else
            echo -e "${RED}Opción inválida. Intenta de nuevo.${NC}"
        fi
    done
}

# Multi-select list (checkboxes style)
# Returns a space-separated string of indices selected (0-indexed)
prompt_multiselect() {
    local title=$1
    shift
    local options=("$@")
    local selected=()
    
    # Initialize all as selected by default (first three items)
    for i in "${!options[@]}"; do
        if [ $i -lt 3 ]; then
            selected[$i]=1
        else
            selected[$i]=0
        fi
    done
    
    while true; do
        clear
        print_banner
        echo -e "${BOLD}$title${NC}"
        echo -e "${BLUE}Usa el número para alternar (con/sin selección). Escribe 'd' (done) para terminar.${NC}\n"
        
        for i in "${!options[@]}"; do
            local checkbox="[ ]"
            if [ "${selected[$i]}" -eq 1 ]; then
                checkbox="[${GREEN}✔${NC}]"
            fi
            echo -e "  $((i+1)). $checkbox ${options[$i]}"
        done
        
        read -p "$(echo -e "\nSelecciona número para alternar, o 'd' para confirmar: ${NC}")" choice
        
        if [ "$choice" = "d" ] || [ "$choice" = "D" ]; then
            break
        elif [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#options[@]}" ]; then
            local idx=$((choice-1))
            if [ "${selected[$idx]}" -eq 1 ]; then
                selected[$idx]=0
            else
                selected[$idx]=1
            fi
        else
            echo -e "${RED}Opción inválida.${NC}"
            sleep 1
        fi
    done
    
    # Return selected indices
    local result=""
    for i in "${!options[@]}"; do
        if [ "${selected[$i]}" -eq 1 ]; then
            result="$result $i"
        fi
    done
    echo "$result"
}

# Spinner helper
show_spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps -p $pid -o state= 2>/dev/null)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}
