const getPull = async (banner) => {
    const response = await fetch(`http://127.0.0.1:5004/banner/pull/${banner.id}`).then(res => res.json())
    return response["pieces"]
}

export default getPull