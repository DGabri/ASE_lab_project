const getAllPieces = async () => {
    const response = await fetch("http://127.0.0.1:5003/piece/all").then(res => res.json())
    return response["pieces"]
}

export default getAllPieces