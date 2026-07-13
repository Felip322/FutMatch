(() => {
    const states = [
        ["AC", "Acre"], ["AL", "Alagoas"], ["AP", "Amapa"], ["AM", "Amazonas"],
        ["BA", "Bahia"], ["CE", "Ceara"], ["DF", "Distrito Federal"], ["ES", "Espirito Santo"],
        ["GO", "Goias"], ["MA", "Maranhao"], ["MT", "Mato Grosso"], ["MS", "Mato Grosso do Sul"],
        ["MG", "Minas Gerais"], ["PA", "Para"], ["PB", "Paraiba"], ["PR", "Parana"],
        ["PE", "Pernambuco"], ["PI", "Piaui"], ["RJ", "Rio de Janeiro"], ["RN", "Rio Grande do Norte"],
        ["RS", "Rio Grande do Sul"], ["RO", "Rondonia"], ["RR", "Roraima"], ["SC", "Santa Catarina"],
        ["SP", "Sao Paulo"], ["SE", "Sergipe"], ["TO", "Tocantins"],
    ];

    const fallbackCities = {
        SP: ["Sao Paulo", "Guarulhos", "Campinas", "Sao Bernardo do Campo", "Santo Andre", "Osasco", "Santos", "Ribeirao Preto", "Sorocaba", "Sao Jose dos Campos"],
        RJ: ["Rio de Janeiro", "Niteroi", "Duque de Caxias", "Nova Iguacu", "Sao Goncalo", "Petropolis", "Volta Redonda"],
        MG: ["Belo Horizonte", "Uberlandia", "Contagem", "Juiz de Fora", "Betim", "Montes Claros", "Uberaba"],
        PR: ["Curitiba", "Londrina", "Maringa", "Ponta Grossa", "Cascavel", "Sao Jose dos Pinhais"],
        RS: ["Porto Alegre", "Caxias do Sul", "Canoas", "Pelotas", "Santa Maria", "Gravatai"],
        SC: ["Florianopolis", "Joinville", "Blumenau", "Sao Jose", "Chapeco", "Itajai"],
        BA: ["Salvador", "Feira de Santana", "Vitoria da Conquista", "Camacari", "Juazeiro", "Lauro de Freitas"],
        PE: ["Recife", "Jaboatao dos Guararapes", "Olinda", "Caruaru", "Petrolina", "Paulista"],
        CE: ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanau", "Sobral", "Crato"],
        GO: ["Goiania", "Aparecida de Goiania", "Anapolis", "Rio Verde", "Trindade"],
        DF: ["Brasilia"],
    };

    const neighborhoods = {
        "SP|SAO PAULO": ["Aclimacao", "Agua Branca", "Bela Vista", "Bom Retiro", "Brooklin", "Butanta", "Campo Belo", "Capao Redondo", "Casa Verde", "Centro", "Consolacao", "Freguesia do O", "Ipiranga", "Itaquera", "Jabaquara", "Lapa", "Liberdade", "Moema", "Mooca", "Morumbi", "Penha", "Perdizes", "Pinheiros", "Santana", "Santo Amaro", "Saude", "Tatuape", "Vila Mariana", "Vila Prudente"],
        "SP|GUARULHOS": ["Centro", "Cocaia", "Gopouva", "Jardim Maia", "Picanço", "Ponte Grande", "Taboao", "Vila Galvao"],
        "SP|CAMPINAS": ["Barao Geraldo", "Cambui", "Centro", "Jardim Chapadao", "Nova Campinas", "Taquaral", "Vila Industrial"],
        "RJ|RIO DE JANEIRO": ["Barra da Tijuca", "Botafogo", "Campo Grande", "Centro", "Copacabana", "Flamengo", "Jacarepagua", "Madureira", "Méier", "Recreio dos Bandeirantes", "Tijuca"],
        "MG|BELO HORIZONTE": ["Barreiro", "Buritis", "Centro", "Funcionarios", "Lourdes", "Pampulha", "Savassi", "Venda Nova"],
    };

    const normalize = (value) => (value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toUpperCase();

    const stateName = (uf) => {
        const item = states.find(([code]) => code === uf);
        return item ? item[1] : uf;
    };

    const fillDatalist = (id, items) => {
        const list = document.getElementById(id);
        if (!list) return;
        list.innerHTML = "";
        items.forEach((item) => {
            const option = document.createElement("option");
            option.value = item;
            list.appendChild(option);
        });
    };

    const cityCache = {};

    const fetchCities = async (uf) => {
        if (!uf) return [];
        if (cityCache[uf]) return cityCache[uf];
        try {
            const response = await fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${uf}/municipios?orderBy=nome`);
            if (!response.ok) throw new Error("IBGE indisponivel");
            const data = await response.json();
            cityCache[uf] = data.map((city) => city.nome);
        } catch (error) {
            cityCache[uf] = fallbackCities[uf] || [];
        }
        return cityCache[uf];
    };

    const relatedField = (field, name) => {
        const form = field.closest("form");
        return form?.querySelector(`[name="${name}"]`) || document.querySelector(`[name="${name}"]`);
    };

    const updateCities = async (stateField) => {
        const uf = normalize(stateField.value).slice(0, 2);
        stateField.value = uf;
        const cities = await fetchCities(uf);
        fillDatalist("brazil-cities-list", cities);
        const cityField = relatedField(stateField, "city");
        if (cityField) {
            cityField.placeholder = uf ? `Cidade de ${stateName(uf)}` : "Cidade";
            cityField.setAttribute("list", "brazil-cities-list");
        }
        updateNeighborhoods(cityField || stateField);
    };

    const updateNeighborhoods = (field) => {
        if (!field) return;
        const form = field.closest("form");
        const stateField = form?.querySelector('[name="state"]') || document.querySelector('[name="state"]');
        const cityField = form?.querySelector('[name="city"]') || document.querySelector('[name="city"]');
        const key = `${normalize(stateField?.value).slice(0, 2)}|${normalize(cityField?.value)}`;
        fillDatalist("brazil-neighborhoods-list", neighborhoods[key] || []);
    };

    const setup = () => {
        fillDatalist("brazil-states-list", states.map(([code, name]) => `${code} - ${name}`));

        document.querySelectorAll('input[name="state"]').forEach((field) => {
            field.setAttribute("list", "brazil-states-list");
            field.setAttribute("maxlength", "2");
            field.placeholder = "SP";
            field.autocomplete = "address-level1";
            field.addEventListener("input", () => {
                field.value = normalize(field.value).slice(0, 2);
            });
            field.addEventListener("change", () => updateCities(field));
            if (field.value) updateCities(field);
        });

        document.querySelectorAll('input[name="city"]').forEach((field) => {
            field.setAttribute("list", "brazil-cities-list");
            field.autocomplete = "address-level2";
            field.addEventListener("focus", () => {
                const stateField = relatedField(field, "state");
                if (stateField) updateCities(stateField);
            });
            field.addEventListener("input", () => updateNeighborhoods(field));
            field.addEventListener("change", () => updateNeighborhoods(field));
        });

        document.querySelectorAll('input[name="neighborhood"]').forEach((field) => {
            field.setAttribute("list", "brazil-neighborhoods-list");
            field.autocomplete = "address-level3";
            field.addEventListener("focus", () => updateNeighborhoods(field));
        });
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setup);
    } else {
        setup();
    }
})();
